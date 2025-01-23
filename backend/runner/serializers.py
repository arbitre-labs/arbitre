from .models import Submission, Test, TestResult
from rest_framework import serializers, validators
import copy
from api.util.serializers import RoleBasedSerializer


class TestSerializer(RoleBasedSerializer):
    class Meta:
        model = Test
        fields = ["id", "exercise", "name", "stdin", "stdout", "coefficient"]

    role_fields = {"teacher": None, "student": ["id", "name"]}


class RawTestsSerializer(serializers.Serializer):
    class Meta:
        fields = ["exercise_id", "raw_tests"]


class SubmissionSerializer(RoleBasedSerializer):
    late = serializers.SerializerMethodField()

    def get_late(self, obj):
        return (
            hasattr(obj, "exercise")
            and obj.exercise.session.deadline
            and obj.created > obj.exercise.session.deadline
        )

    class Meta:
        model = Submission
        fields = ["id", "exercise", "file", "status", "created", "late", "grade"]
        read_only_fields = ["grade"]

    def run_validators(self, value):
        for validator in copy.copy(self.validators):
            if isinstance(validator, validators.UniqueTogetherValidator):
                self.validators.remove(validator)
        super(SubmissionSerializer, self).run_validators(value)

    role_fields = {
        "teacher": None,
        "student": None,
    }


class TestResultSerializer(RoleBasedSerializer):
    # nested serializers for reading
    submission = SubmissionSerializer(read_only=True)
    exercise_test = TestSerializer(read_only=True)

    # primary key fields for writing
    submission_pk = serializers.PrimaryKeyRelatedField(
        queryset=Submission.objects.all(), source="submission", write_only=True
    )
    exercise_test_pk = serializers.PrimaryKeyRelatedField(
        queryset=Test.objects.all(), source="exercise_test", write_only=True
    )

    class Meta:
        model = TestResult
        fields = (
            "id",
            "submission",
            "submission_pk",
            "exercise_test",
            "exercise_test_pk",
            "stdout",
            "time",
            "memory",
            "status",
            "token",
        )

    role_fields = {
        "teacher": None,
        "student": [
            "exercise_test",
            "id",
            "memory",
            "status",
            "stdout",
            "submission",
            "time",
        ],
    }

    def run_validators(self, value):
        for validator in copy.copy(self.validators):
            if isinstance(validator, validators.UniqueTogetherValidator):
                self.validators.remove(validator)
        super(TestResultSerializer, self).run_validators(value)

    def create(self, validated_data):
        testresult, created = TestResult.objects.get_or_create(
            submission=validated_data["submission"],
            exercise_test=validated_data["exercise_test"],
            defaults={
                "submission": validated_data["submission"],
                "exercise_test": validated_data["exercise_test"],
            },
        )

        if "token" in validated_data:
            testresult.token = validated_data["token"]

        testresult.status = validated_data["status"]
        if testresult.status in ["pending", "running"]:
            testresult.stdout = ""
            testresult.time = -1
            testresult.memory = -1
        else:
            testresult.stdout = validated_data.get("stdout", "")
            testresult.time = validated_data.get("time", -1)
            testresult.memory = validated_data.get("memory", -1)

        testresult.save()

        return testresult
