from .models import Submission, Test, TestResult
from api.models import Exercise, Session, Course, StudentGroup
from django.contrib import admin


# Register your models here.
class StudentGroupInline(admin.StackedInline):
    model = StudentGroup
    extra = 0
    filter_horizontal = ["students"]


class StudentGroupAdmin(admin.ModelAdmin):
    fields = ["name", "course", "students"]
    filter_horizontal = ["students"]
    list_display = ["name", "course"]
    list_filter = ["course"]
    search_fields = ["name", "course"]


class TestInline(admin.StackedInline):
    model = Test
    extra = 1


class ExerciseAdmin(admin.ModelAdmin):
    fields = [
        "session",
        "title",
        "description",
        "prefix",
        "suffix",
        "type",
        "grade",
        "teacher_files",
    ]
    list_display = ["title", "session", "type", "grade"]
    list_filter = ["session", "type"]
    inlines = [TestInline]


class SubmissionAdmin(admin.ModelAdmin):
    fields = ["exercise", "owner", "file", "created", "status"]
    readonly_fields = ["file", "created"]
    list_display = ["exercise", "owner", "status", "created"]
    list_filter = ["status", "exercise", "owner", "created"]
    search_fields = ["exercise", "owner", "status"]


class CourseAdmin(admin.ModelAdmin):
    fields = [
        "id",
        "title",
        "description",
        "join_code",
        "join_code_enabled",
        "students",
        "owners",
        "tutors",
        "language",
        "groups_enabled",
        "auto_groups_enabled",
        "late_penalty",
    ]
    filter_horizontal = [
        "students",
        "owners",
        "tutors",
    ]
    readonly_fields = ["id"]
    list_display = [
        "title",
        "join_code",
        "id",
    ]
    inlines = [StudentGroupInline]


class TestResultAdmin(admin.ModelAdmin):
    fields = ["status", "id", "submission", "exercise_test", "stdout", "token"]
    readonly_fields = ["id", "submission", "exercise_test", "stdout", "token"]
    list_display = ["id", "submission", "status", "exercise_test", "stdout"]
    list_filter = ["status"]


admin.site.register(Submission, SubmissionAdmin)
admin.site.register(TestResult, TestResultAdmin)

admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Session)
admin.site.register(Course, CourseAdmin)
admin.site.register(StudentGroup, StudentGroupAdmin)
