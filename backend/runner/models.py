from api.models import Exercise
from asgiref.sync import async_to_sync
from celery import Celery
from channels.layers import get_channel_layer
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum, Case, When, F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing_extensions import Optional
import environ
import os
import random
import uuid


class Submission(models.Model):
    """
    The stored code file that will be judged
    """

    class SubmissionStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        RUNNING = "running", _("Running")
        SUCCESS = "success", _("Success")
        FAILED = "failed", _("Failed")
        ERROR = "error", _("Error")

    def get_file_name(self, _):
        path = "uploads"
        extension = self.file.name.split(".")[-1]

        exercise = self.exercise
        created_with_correct_timezone = timezone.localtime(self.created)
        created_month_day_hour_minutes_seconds = created_with_correct_timezone.strftime(
            "%m-%d_%H-%M-%S"
        )

        format = (
            exercise.title[0:10]
            + "_"
            + self.owner.username[0:10]
            + "_"
            + created_month_day_hour_minutes_seconds
            + "."
            + extension
        )

        return os.path.join(path, format)

    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_file_name)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING,
    )
    created = models.DateTimeField(auto_now=True)
    ignore = models.BooleanField(default=False, blank=True)
    grade = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.file.name

    def refresh_status(self):
        # Refresh submission status

        old_status = self.status

        test_results = TestResult.objects.filter(submission=self)
        status = ""
        if test_results:
            statuses = set([result.status for result in test_results])

            if statuses == set(["success"]):
                status = "success"
            elif "error" in statuses:
                status = "error"
            elif "failed" in statuses:
                status = "failed"
            elif "pending" in statuses:
                status = "pending"
            else:
                status = "running"
        else:
            status = "pending"
        submission = Submission.objects.filter(pk=self.id)
        submission.update(status=status)

        self.refresh_grade()

        if status != old_status:
            print(f"Submission status changed : {old_status} -> {status}")

            # Send WebSocket update
            channel_layer = get_channel_layer()

            from arbitre.util import prepare_submission_message

            message = prepare_submission_message(self.id)

            async_to_sync(channel_layer.group_send)(
                f"submission_{self.exercise.id}_{self.owner.id}", message
            )

    def _update_grade(self, grade: Optional[Decimal]):
        """
        Helper function for updating grade field

        NOTE : Not using `save()` because it triggers testing
        """

        Submission.objects.filter(pk=self.id).update(grade=grade)

    def refresh_grade(self):
        test_results = TestResult.objects.filter(submission=self).select_related(
            "exercise_test__exercise__session__course"
        )

        if not test_results.exists():
            self._update_grade(None)
            return

        exercise = test_results.first().exercise_test.exercise
        if not exercise.grade:
            self._update_grade(None)
            return

        # Compute grade using aggregation
        grade_calculation = test_results.aggregate(
            sum_of_coefficients=Sum("exercise_test__coefficient"),
            successful_tests=Sum(
                Case(
                    When(status="success", then=F("exercise_test__coefficient")),
                    default=0,
                )
            ),
        )

        sum_of_coefficients = grade_calculation["sum_of_coefficients"]
        successful_tests = grade_calculation["successful_tests"]

        if not sum_of_coefficients:
            self._update_grade(None)
            return

        grade = (Decimal(successful_tests) / Decimal(sum_of_coefficients)) * Decimal(
            exercise.grade
        )

        session = exercise.session

        if session.deadline and session.deadline < self.created:
            late_penalty = Decimal(session.course.late_penalty) / Decimal(100)
            grade *= 1 - late_penalty

        self._update_grade(grade)

    def save(self, *args, **kwargs):
        if self.ignore:
            super(Submission, self).save(*args, **kwargs)
            return

        celery = Celery("arbitre", include=["arbitre.tasks"])

        exercise = self.exercise
        course = exercise.session.course
        tests = Test.objects.filter(exercise=self.exercise)

        type = exercise.type

        prefix = exercise.prefix
        suffix = exercise.suffix

        # Read env
        env = environ.Env()
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        environ.Env.read_env(env_file=env_file)

        # decide Judge0 host to use
        hosts = env.list("JUDGE0_HOSTNAMES", default=["localhost"])
        host = random.choice(hosts)

        # put all former tests (if any) in pending state
        # using save() in a for loop instead of update() on the queryset, because it would skip save()
        test_results = TestResult.objects.filter(submission__id=self.id)
        for test_result in test_results:
            test_result.status = Submission.SubmissionStatus.PENDING
            test_result.memory = -1
            test_result.time = -1
            test_result.stdout = ""
            test_result.save()

        self.refresh_status()

        if tests:
            super(Submission, self).save(*args, **kwargs)

            file_content = ""

            if type == "single":
                with self.file.open(mode="rb") as f:
                    file_content = f.read().decode("utf-8", "ignore")

            elif type == "multiple":
                # convert zip file to base64
                import base64

                with self.file.open(mode="rb") as f:
                    file_content = base64.b64encode(f.read()).decode("utf-8", "ignore")

            else:
                raise Exception("Invalid exercise type")

            for test in tests:
                # Add Judge0 task to queue
                celery.send_task(
                    "arbitre.tasks.run_test",
                    (
                        host,
                        type,
                        self.id,
                        test.id,
                        file_content,
                        prefix,
                        suffix,
                        course.language,
                    ),
                )
        else:
            self.status = Submission.SubmissionStatus.SUCCESS
            super(Submission, self).save(*args, **kwargs)
            self.refresh_status()

    class Meta:
        unique_together = ("exercise", "owner")


class Test(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default="")
    stdin = models.TextField(default="", blank=True)
    stdout = models.TextField(default="", blank=True)
    coefficient = models.IntegerField(blank=True, null=True, default=1)
    # TODO add all test criterias

    def __str__(self):
        return self.name + " (" + str(self.exercise) + ")"

    class Meta:
        unique_together = ("exercise", "name")


class TestResult(models.Model):
    """
    A test, ran on a file
    """

    class TestResultStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        RUNNING = "running", _("Running")
        SUCCESS = "success", _("Success")
        FAILED = "failed", _("Failed")
        ERROR = "error", _("Error")

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    token = models.TextField(
        unique=True, default=uuid.uuid4, editable=True
    )  # Judge0 token, used for callback. Populated with a random uuid just for initialization.
    exercise_test = models.ForeignKey(Test, on_delete=models.CASCADE)
    stdout = models.TextField(default="")
    time = models.FloatField(default=-1)
    memory = models.IntegerField(default=-1)
    status = models.CharField(
        max_length=10,
        choices=TestResultStatus.choices,
        default=TestResultStatus.PENDING,
    )

    class Meta:
        unique_together = ("submission", "exercise_test")

    def __str__(self):
        return (
            self.submission.exercise.title
            + " : "
            + self.exercise_test.name
            + " ("
            + str(self.submission.owner)
            + ")"
        )

    def save(self, *args, **kwargs):
        super(TestResult, self).save(*args, **kwargs)
        self.submission.refresh_status()

        # Get group to send to
        channel_layer = get_channel_layer()
        channels_group = (
            f"submission_{self.exercise_test.exercise.id}_{self.submission.owner.id}"
        )

        from arbitre.util import prepare_test_result_message

        message = prepare_test_result_message(self.id)

        async_to_sync(channel_layer.group_send)(channels_group, message)

    def run_all_pending_testresults():
        celery = Celery("arbitre", include=["arbitre.tasks"])

        pending_testresults = TestResult.objects.filter(
            status=TestResult.TestResultStatus.PENDING
        ).prefetch_related("submission", "exercise_test")

        if len(pending_testresults) == 0:
            return

        print("Running all pending testresults...")

        # Read env
        env = environ.Env()
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        environ.Env.read_env(env_file=env_file)

        # decide judge0 host to use
        hosts = env.list("JUDGE0_HOSTNAMES", default=["localhost"])
        host = random.choice(hosts)

        for testresult in pending_testresults:
            submission = testresult.submission
            if submission.ignore:
                print(f"Submission {submission.id} ({submission.owner}) ignored")
                continue
            exercise_test = testresult.exercise_test

            print(
                f"Re-running testresult {testresult.id} (status: {testresult.status}) in {submission.id} by {submission.owner} (created {submission.created}, submission status {submission.status})"
            )

            # Read file content
            file_content = ""

            if submission.exercise.type == "single":
                with submission.file.open(mode="rb") as f:
                    file_content = f.read().decode("utf-8", "ignore")

            elif submission.exercise.type == "multiple":
                # convert zip file to base64
                import base64

                with submission.file.open(mode="rb") as f:
                    file_content = base64.b64encode(f.read()).decode("utf-8", "ignore")

            lang = submission.exercise.session.course.language
            type = submission.exercise.type
            prefix = submission.exercise.prefix
            suffix = submission.exercise.suffix

            # if submission created more than 20 seconds ago
            if submission.created < timezone.now() - timedelta(seconds=20):
                # Add Judge0 task to queue
                celery.send_task(
                    "arbitre.tasks.run_test",
                    (
                        host,
                        type,
                        submission.id,
                        exercise_test.id,
                        file_content,
                        prefix,
                        suffix,
                        lang,
                    ),
                )

        print(f"Ran {len(pending_testresults)} pending testresults")
