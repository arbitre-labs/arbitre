from .models import Submission, Test, TestResult
from api.models import Exercise
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from runner.serializers import (
    RawTestsSerializer,
    SubmissionSerializer,
    TestResultSerializer,
    TestSerializer,
)
from api.util.views import RoleBasedViewSet
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, ParseError
import base64
import json


class SubmissionViewSet(RoleBasedViewSet):
    # permission_classes = [permissions.IsAuthenticated]

    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer

    def perform_create(self, serializer):
        # Check if there's a hard deadline and if it's passed
        session = serializer.validated_data["exercise"].session
        if (
            session.deadline_type == "hard"
            and session.deadline is not None
            and session.deadline < timezone.now()
        ):
            raise serializers.ValidationError(
                {"detail": "Hard deadline passed, can't submit"}
            )

        # Create submission or update it if it already exists
        submission, created = Submission.objects.update_or_create(
            exercise_id=self.request.data["exercise"],
            owner=self.request.user,
            defaults={
                "file": self.request.data["file"],
                "status": Submission.SubmissionStatus.PENDING,
            },
        )

    # Get submission for  exercise if exercise_id is given
    def get_queryset(self):
        exercise_id = self.request.query_params.get("exercise_id", None)
        user_id = self.request.query_params.get("user_id", None)
        if user_id:
            user = User.objects.get(pk=user_id)
        else:
            user = self.request.user
        if exercise_id:
            queryset = Submission.objects.filter(exercise=exercise_id, owner=user)
        elif user_id:
            queryset = Submission.objects.filter(owner=user)
        else:
            queryset = Submission.objects.all()
        return queryset


class RefreshSubmissionViewSet(viewsets.ViewSet):
    """
    Refreshes submission status based on all test results statuses for that submission
    """

    permission_classes = [permissions.IsAuthenticated]

    # GET runner/api/refresh-submission?submission_id=...
    def list(self, request):
        try:
            # if all=true parameter passed, refresh all submissions

            if request.query_params.get("all") == "true":
                submissions = Submission.objects.all()
            else:
                submissions = Submission.objects.filter(
                    pk=request.query_params["submission_id"]
                )

            for submission in submissions:
                test_results = TestResult.objects.filter(submission=submission)
                status = ""
                if test_results:
                    if all([result.status == "success" for result in test_results]):
                        status = "success"
                    elif any([result.status == "failed" for result in test_results]):
                        status = "failed"
                    elif any([result.status == "error" for result in test_results]):
                        status = "error"
                    else:
                        status = "running"
                else:
                    status = "pending"
                Submission.objects.filter(pk=submission.id).update(status=status)

            return JsonResponse({"detail": "Submission status updated"})

        except Submission.DoesNotExist:
            return JsonResponse({"status": "Not Found"})


class SubmissionFileViewSet(viewsets.ViewSet):
    """
    Returns submission file with content
    """

    permission_classes = [permissions.IsAuthenticated]

    # GET runner/api/submission-file?submission_id=...
    def list(self, request):
        error_response = JsonResponse(
            {"file": "Not Found", "content": "", "language": "", "type": "not-found"}
        )

        try:
            submission = Submission.objects.select_related(
                "exercise", "exercise__session", "exercise__session__course"
            ).get(pk=request.query_params["submission_id"])

            type = submission.exercise.type
            language = submission.exercise.session.course.language

            if (
                request.user != submission.owner
                and request.user not in submission.exercise.session.course.owners.all()
                and request.user not in submission.exercise.session.course.tutors.all()
            ):
                return error_response

            try:
                with submission.file.open(mode="rb") as f:
                    if type == "single":
                        file_content = f.read().decode("utf-8", "ignore")
                    elif type == "multiple":
                        # Get zip file, encode it in base64 and return it
                        import base64

                        file_content = base64.b64encode(f.read()).decode(
                            "utf-8", "ignore"
                        )
                    else:
                        return error_response
            except FileNotFoundError:
                return error_response

            return JsonResponse(
                {
                    "file": str(submission.file),
                    "content": file_content,
                    "language": language,
                    "type": type,
                }
            )

        except Submission.DoesNotExist:
            return error_response


class RequeueSubmissionsViewSet(viewsets.ViewSet):
    """
    Requeues all submissions for a given exercise
    """

    permission_classes = [permissions.IsAuthenticated]

    # GET runner/api/requeue-submissions?exercise_id=...
    def list(self, request):
        try:
            submissions = Submission.objects.filter(
                exercise_id=request.query_params["exercise_id"]
            )

            # Get all test results for the submissions and set their status to "pending"
            TestResult.objects.filter(
                submission__exercise_id=request.query_params["exercise_id"]
            ).update(status="pending", stdout="")

            # Set all submissions to pending
            for submission in submissions:
                Submission.objects.filter(pk=submission.id).update(status="pending")

            return JsonResponse({"detail": "Submissions requeued"})

        except Submission.DoesNotExist:
            return JsonResponse({"status": "Not Found"})


class RawTestsViewSet(viewsets.ModelViewSet):
    """
    Lets teachers manage tests in a raw object format (JSON).

    body: {
        "exercise_id": 1,
        "raw_tests": "{'test1': {'stdin': '1','stdout': '2'}, 'test2': {'stdin': '3','stdout': '4'}}"
    }
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RawTestsSerializer

    def perform_create(self, serializer):
        user = self.request.user

        exercise_id = self.request.data.get("exercise_id")
        exercise = Exercise.objects.get(id=exercise_id)

        if user not in exercise.session.course.owners.all():
            raise ValidationError("You are not the owner of this course")

        # Parse the raw tests string first
        raw_tests = self.request.data.get("raw_tests")
        tests = json.loads(raw_tests)

        # Check that every object has the correct keys only
        for test in tests:
            if set(test) != set(["name", "stdin", "stdout"]):
                raise ParseError("Malformed data")

        # Delete all former tests
        for test in Test.objects.filter(exercise__id=exercise_id).all():
            test.delete()

        # Create new objects
        for test in tests:
            Test.objects.create(
                exercise=exercise,
                name=test.get("name"),
                stdin=test.get("stdin"),
                stdout=test.get("stdout"),
            )


class TestViewSet(RoleBasedViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    # permission_classes = [permissions.IsAuthenticated | HasAPIKey]

    # Get the tests for the exercise if exercise_id is given
    def get_queryset(self):
        queryset = Test.objects.all()
        exercise_id = self.request.query_params.get("exercise_id", None)
        if exercise_id:
            queryset = queryset.filter(exercise=exercise_id)
        return queryset

    def perform_create(self, serializer):
        # Take all the submissions for this exercise and add a pending test with the new test
        test = serializer.save()

        for submission in Submission.objects.filter(
            exercise_id=self.request.data["exercise"]
        ):
            TestResult.objects.create(
                submission=submission,
                exercise_test=test,
                status="pending",
            )

        # Take all associated submissions and refresh their statuses
        for submission in Submission.objects.filter(
            exercise_id=self.request.data["exercise"]
        ):
            submission.refresh_status()

        return super().perform_create(serializer)

    def perform_update(self, serializer):
        # Take all test results for this exercise and this test and set their status to "pending"
        TestResult.objects.filter(
            submission__exercise_id=self.request.data["exercise"],
            exercise_test=self.request.data["id"],
        ).update(status="pending", stdout="")

        # Take all associated submissions and refresh their statuses
        for submission in Submission.objects.filter(
            exercise_id=self.request.data["exercise"]
        ):
            submission.refresh_status()

        serializer.save()
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        # Take all associated submissions and refresh their statuses
        exercise_id = instance.exercise.id
        for submission in Submission.objects.filter(exercise_id=exercise_id):
            submission.refresh_status()

        return super().perform_destroy(instance)


class TestResultViewSet(viewsets.ModelViewSet):
    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer

    # GET runner/api?exercise_id=...
    def get_queryset(self):
        exercise_id = self.request.query_params.get("exercise_id")

        if exercise_id:
            if self.request.query_params.get("user_id"):
                user_id = self.request.query_params.get("user_id")
            else:
                user_id = self.request.user.id

            return self.queryset.filter(
                submission__exercise_id=exercise_id, submission__owner=user_id
            )
        else:
            return super().get_queryset()


class Judge0CallbackView(APIView):
    """
    Handles Judge0's callback on submission completion.
    Processes the execution results and updates the corresponding TestResult.
    """

    # PUT
    def put(self, request, *args, **kwargs):
        # Check host
        host = request.META.get("HTTP_HOST").split(":")[0]
        if host not in settings.ALLOWED_HOSTS:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        token = request.data.get("token")
        if not token:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            test_result = TestResult.objects.select_related("exercise_test").get(
                token=token
            )
        except TestResult.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        test = test_result.exercise_test
        output_data = request.data

        # Decode and concatenate all output streams
        stdout = ""
        for key in ["message", "stdout", "stderr", "compile_output"]:
            if output_data.get(key):
                stdout += base64.b64decode(output_data[key]).decode("utf-8")

        # Determine execution status
        status_value = "error"
        if output_data.get("stdout"):
            decoded_stdout = base64.b64decode(output_data["stdout"]).decode("utf-8")
            if not test.stdout or decoded_stdout.rstrip("\n") == test.stdout:
                status_value = "success"
            else:
                status_value = "failed"

        # Update test result
        test_result.stdout = stdout
        test_result.status = status_value
        test_result.time = output_data.get("time") or 0
        test_result.memory = output_data.get("memory") or 0
        test_result.save()

        return Response(status=status.HTTP_200_OK)
