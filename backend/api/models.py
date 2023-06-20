from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    """
    A course, that includes sessions, owned by a teacher
    """

    class Languages(models.TextChoices):
        ADA = "ada", _("Ada")
        C = "c", _("C")
        CPP = "c++", _("C++")
        CSHARP = "c#", _("C#")
        D = "d", _("D")
        GO = "go", _("Go")
        HASKELL = "haskell", _("Haskell")
        JAVA = "java", _("Java")
        JAVASCRIPT = "javascript", _("JavaScript")
        LUA = "lua", _("Lua")
        OCAML = "ocaml", _("OCaml")
        PASCAL = "pascal", _("Pascal")
        PERL = "perl", _("Perl")
        PHP = "php", _("PHP")
        PROLOG = "prolog", _("Prolog")
        PYTHON = "python", _("Python")
        RUBY = "ruby", _("Ruby")
        RUST = "rust", _("Rust")
        SCHEME = "scheme", _("Scheme")

    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    language = models.CharField(
        max_length=10,
        choices=Languages.choices,
        default=Languages.PYTHON,
    )
    students = models.ManyToManyField(
        User, related_name="%(class)s_courses_students", blank=True
    )
    owners = models.ManyToManyField(
        User,
        related_name="%(class)s_courses_owners",
    )
    tutors = models.ManyToManyField(
        User,
        related_name="%(class)s_courses_tutors",
        blank=True,
    )
    join_code = models.CharField(max_length=8, blank=False, default="00000000")
    join_code_enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class StudentGroup(models.Model):
    """
    A group of students, related to one course.
    """

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    students = models.ManyToManyField(User, related_name="%(class)s_students")

    def __str__(self):
        return f"{self.name} ({self.course.title})"

    # TODO check if student in course
    # TODO check if student not in other group of course


class Session(models.Model):
    """
    A part of a course, that includes exercises
    """

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.course.title + " : " + self.title


class Exercise(models.Model):
    """
    The exercise given to the student
    """

    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    prefix = models.TextField(blank=True)
    suffix = models.TextField(blank=True)

    def __str__(self):
        return self.title
