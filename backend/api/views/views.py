from ..models import Course, Session, Exercise, StudentGroup
from ..serializers import (
    CourseSerializer,
    ExerciseSerializer,
    MinimalExerciseSerializer,
    SessionSerializer,
    StudentGroupSerializer,
)
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from runner.models import Submission
from runner.models import TestResult
from runner.serializers import SubmissionSerializer
from runner.serializers import TestResultSerializer
from django.utils import timezone
import json


class IsCourseOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.user in obj.course.owners.all()
            or request.user in obj.course.tutors.all()
        )


class HasSessionStarted(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if obj.start_date is None:
            return True
        return obj.start_date < timezone.now()


class SessionViewSet(viewsets.ModelViewSet):
    """
    Manage sessions.

    List all sessions (GET), or create a new session (POST).

    body : {
        course_id: 1,
        title: "Session 1",
        description: "This is the first session"
    }
    """

    serializer_class = SessionSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsCourseOwner]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [
                permissions.IsAuthenticated,
                HasSessionStarted | IsCourseOwner,
            ]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    # Return sessions of course if course_id param passed. Else, return all sessions
    def get_queryset(self):
        course_id = self.request.query_params.get("course_id")

        if course_id:
            # If owner, return all sessions
            if (
                self.request.user in Course.objects.get(id=course_id).owners.all()
                or self.request.user in Course.objects.get(id=course_id).tutors.all()
            ):
                return Session.objects.filter(course_id=course_id)
            # Else, return all sessions. If a session does have a start date, return only sessions that have started
            else:
                return Session.objects.filter(
                    Q(course_id=course_id)
                    & (Q(start_date__isnull=True) | Q(start_date__lt=timezone.now()))
                )
        else:
            return Session.objects.all()


class ExerciseViewSet(viewsets.ModelViewSet):
    """
    List all exercises (GET), or create a new exercise (POST).
    """

    serializer_class = ExerciseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    # Return exercises of session if course_id param passed. Else, return all sessions
    def get_queryset(self):
        session_id = self.request.query_params.get("session_id")

        response = []

        if session_id:
            response = Exercise.objects.filter(session_id=session_id)
        else:
            response = Exercise.objects.all()

        # If not owner/tutor, only return exercises that have started

        if response:
            course = Course.objects.filter(session__exercise__in=response)[0]

            if (
                self.request.user not in course.owners.all()
                and self.request.user not in course.tutors.all()
            ):
                response = response.filter(
                    Q(session__start_date__isnull=True)
                    | Q(session__start_date__lt=timezone.now())
                )

        return response


class StudentGroupViewSet(viewsets.ModelViewSet):
    """
    Manage Student Groups.

    Set the whole student group at once.

    GET all student groups of a course (GET)
    params :
    - course_id : id of the course (number)
    """

    serializer_class = StudentGroupSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        course_id = self.request.query_params.get("course_id", None)
        if course_id:
            return StudentGroup.objects.filter(course=course_id)
        else:
            return StudentGroup.objects.all()

    def create(self, request, *args, **kwargs):
        course = Course.objects.get(id=request.data.get("course"))

        if request.user not in course.owners.all():
            return Response(
                {"message": "Forbidden: User is not an owner"},
                status=status.HTTP_403_FORBIDDEN,
            )

        student_group = super().create(request, *args, **kwargs)

        return Response(
            {
                "message": "Student group created",
                "student_group": student_group.data,
                "course": CourseSerializer(course).data,
            },
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        course = self.get_object().course
        user = request.user

        if user not in course.owners.all():
            return Response(
                {"message": "Forbidden: User is not an owner"},
                status=status.HTTP_403_FORBIDDEN,
            )

        student_group = super().update(request, *args, **kwargs)

        return Response(
            {
                "message": "Student group updated",
                "student_group": student_group.data,
                "course": CourseSerializer(course).data,
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        course = self.get_object().course

        if request.user not in course.owners.all():
            return Response(
                {"message": "Forbidden: User is not an owner"},
                status=status.HTTP_403_FORBIDDEN,
            )

        super().destroy(request, *args, **kwargs)

        return Response(
            {
                "message": "Student group deleted",
                "course": CourseSerializer(course).data,
            },
            status=status.HTTP_200_OK,
        )


class SetStudentGroupViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request):
        student = User.objects.get(id=request.data.get("user_id"))
        student_group = StudentGroup.objects.get(id=request.data.get("student_group"))
        course = student_group.course

        if request.user not in course.owners.all():
            return Response(
                {"message": "Forbidden: User is not an owner"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if student not in course.students.all():
            return Response(
                {"message": "Forbidden: User is not a student of the course"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Remove student from previous group
        previous_group = StudentGroup.objects.filter(
            students__in=[student], course=course
        ).first()
        if previous_group:
            previous_group.students.remove(student)
            previous_group.save()

        # Add student to new group
        student_group.students.add(student)
        student_group.save()

        return Response(
            {
                "message": "Student added to group",
                "course": CourseSerializer(course).data,
            },
            status=status.HTTP_200_OK,
        )


class CoursesSessionsExercisesViewSet(viewsets.ViewSet):
    """
    Return all courses, sessions and exercises.

    GET : Get all courses, sessions and exercises of current user
    """

    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        user = request.user

        courses = Course.objects.filter(
            Q(tutors__in=[user]) | Q(owners__in=[user])
        ).distinct()

        courses_data = []
        for course in courses:
            sessions = Session.objects.filter(course=course)
            sessions_data = []
            for session in sessions:
                exercises = Exercise.objects.filter(session=session)
                exercises_data = []
                for exercise in exercises:
                    exercises_data.append(
                        {
                            "id": exercise.id,
                            "title": exercise.title,
                        }
                    )

                sessions_data.append(
                    {
                        "id": session.id,
                        "title": session.title,
                        "exercises": exercises_data,
                    }
                )

            courses_data.append(
                {
                    "id": course.id,
                    "title": course.title,
                    "sessions": sessions_data,
                    "student_groups": StudentGroupSerializer(
                        StudentGroup.objects.filter(course=course), many=True
                    ).data,
                }
            )

        return Response(courses_data)


class ResultsOfSessionViewSet(viewsets.ViewSet):
    """
    Get results of a session.

    Get submission statuses for all exercises of a session, for a given user.
    Params:
    - user_id : number
    - session_id : number
    """

    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        user = User.objects.get(id=request.data["user_id"])
        session = Session.objects.get(id=request.data["session_id"])

        # Get all the exercises to do in the session
        exercises = Exercise.objects.filter(session=session)
        exercises_to_do = MinimalExerciseSerializer(instance=exercises, many=True)
        exercises_to_do_dict = json.loads(json.dumps(exercises_to_do.data))

        # Get status for exercises that have been submitted
        submissions = Submission.objects.filter(owner=user, exercise__in=exercises)
        submissions_serializer = SubmissionSerializer(submissions, many=True)

        # Return exercise and status only
        results = []
        for exercise in exercises_to_do_dict:
            status = "not submitted"

            for submission in submissions_serializer.data:
                if submission["exercise"] == exercise["id"]:
                    status = submission["status"]

            # Get status for exercise tests
            testResults = TestResult.objects.filter(
                submission__owner=user, submission__exercise_id=exercise["id"]
            )
            testResults_serializer = TestResultSerializer(testResults, many=True)

            results.append(
                {
                    "exercise_id": exercise["id"],
                    "exercise_title": exercise["title"],
                    "status": status,
                    "testResults": testResults_serializer.data,
                }
            )

        return Response(results)


class AllResultsOfSessionViewSet(viewsets.ViewSet):
    """
    Get results of a session.

    Get submission statuses for all exercises of a session, for all students.
    Params:
    - session_id :  number
    - groups :      array (?groups=1,2,3) (optional)

    Used to create a table of results for a session.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        session = Session.objects.get(id=self.request.GET.get("session_id"))

        if "groups" in self.request.GET and self.request.GET.get("groups") != "":
            groups = []
            for group_id in self.request.GET.get("groups").split(","):
                group = StudentGroup.objects.get(id=group_id)
                groups.append(group)

            # Check if the groups exist and belong to the course
            for group in groups:
                if (
                    group not in StudentGroup.objects.all()
                    or group.course != session.course
                ):
                    return Response(
                        {"message": "NOT FOUND: Group not found or not in course"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            students = []
            for group in groups:
                for student in group.students.all():
                    students.append(student)

        else:
            students = session.course.students.all()
        students_ids = [student.id for student in students]

        students_data = []
        for student_id in students_ids:
            result_request = HttpRequest()
            result_request.method = "GET"
            result_request.data = {
                "user_id": student_id,
                "session_id": session.id,
            }

            result_response = ResultsOfSessionViewSet.list(self, result_request).data

            try:
                student_group = StudentGroup.objects.get(
                    students__in=[student_id], course=session.course
                ).id
            except StudentGroup.DoesNotExist:
                student_group = None

            students_data.append(
                {
                    "user_id": student_id,
                    "username": User.objects.get(id=student_id).username,
                    "group": student_group,
                    "exercises": result_response,
                }
            )

        return Response(students_data)


class AllResultsViewSet(viewsets.ViewSet):
    """
    Get all results of a teacher's courses.

    Get submission statuses for all exercises for all students of all user's courses.
    User : logged in user

    Used to create a table of results for all courses.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        user = self.request.user
        courses = Course.objects.filter(
            Q(owners__in=[user]) | Q(tutors__in=[user])
        ).distinct()

        courses_to_send = []

        for course in courses:
            all_students = course.students.all()
            all_students_ids = [student.id for student in all_students]

            session_data = []

            for session in course.session_set.all():
                students_data = []
                for student_id in all_students_ids:
                    result_request = HttpRequest()
                    result_request.method = "GET"
                    result_request.data = {
                        "user_id": student_id,
                        "session_id": session.id,
                    }

                    result_response = ResultsOfSessionViewSet.list(
                        self, result_request
                    ).data

                    students_data.append(
                        {
                            "student_id": student_id,
                            "student_name": User.objects.get(id=student_id).username,
                            "results": result_response,
                        }
                    )

                session_data.append(
                    {
                        "session_id": session.id,
                        "session_title": session.title,
                        "students_data": students_data,
                    }
                )

            courses_to_send.append(
                {
                    "course_id": course.id,
                    "course_title": course.title,
                    "sessions": session_data,
                }
            )

        return Response({"courses": courses_to_send})
