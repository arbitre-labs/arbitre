from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Course(models.Model):
    """
    A course, that includes sessions, owned by a teacher
    """

    class Languages(models.TextChoices):
        ASM = "asm", _("Assembly")
        BASH = "bash", _("Bash")
        BASIC = "basic", _("Basic")
        C = "c", _("C")
        CPP = "cpp", _("C++")
        CSHARP = "csharp", _("C#")
        CLOJURE = "clojure", _("Clojure")
        COBOL = "cobol", _("Cobol")
        COMMON_LISP = "commonlisp", _("Common Lisp")
        D = "d", _("D")
        ELIXIR = "elixir", _("Elixir")
        ERLANG = "erlang", _("Erlang")
        EXECUTABLE = "executable", _("Executable")
        FORTRAN = "fortran", _("Fortran")
        FSHARP = "fsharp", _("F#")
        GO = "go", _("Go")
        GROOVY = "groovy", _("Groovy")
        HASKELL = "haskell", _("Haskell")
        JAVA = "java", _("Java")
        JAVASCRIPT = "javascript", _("JavaScript")
        KOTLIN = "kotlin", _("Kotlin")
        LUA = "lua", _("Lua")
        OBJECTIVE_C = "objectivec", _("Objective-C")
        OCAML = "ocaml", _("OCaml")
        OCTAVE = "octave", _("Octave")
        PASCAL = "pascal", _("Pascal")
        PERL = "perl", _("Perl")
        PHP = "php", _("PHP")
        PROLOG = "prolog", _("Prolog")
        PYTHON = "python", _("Python")
        R = "r", _("R")
        RUBY = "ruby", _("Ruby")
        RUST = "rust", _("Rust")
        SCALA = "scala", _("Scala")
        SQL = "sql", _("SQL")
        SWIFT = "swift", _("Swift")
        TYPESCRIPT = "typescript", _("TypeScript")
        VBNET = "vbnet", _("VB.NET")

    id: int
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

    groups_enabled = models.BooleanField(default=False)
    auto_groups_enabled = models.BooleanField(default=False)

    late_penalty = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )

    def __str__(self):
        return self.title

    def handle_student_groups_change(self, *args, **kwargs):
        """
        Handle changes in student groups, and update them if necessary.

        This method is called when a course is saved, and when a student group is saved or deleted.
        Former course and student groups are compared to new ones, and if they are different, the groups are updated.
        """

        former_course = Course.objects.get(pk=self.pk)
        former_student_groups = StudentGroup.objects.filter(course=self)

        super(Course, self).save(*args, **kwargs)

        new_course = Course.objects.get(pk=self.pk)
        new_student_groups = StudentGroup.objects.filter(course=self)

        if self.auto_groups_enabled and (
            former_course.auto_groups_enabled != new_course.auto_groups_enabled
            or former_course.students != new_course.students
            or former_student_groups != new_student_groups
        ):
            self.make_auto_groups()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            self.handle_student_groups_change(*args, **kwargs)

            # Get submissions related to this course
            # And update their grades
            # TODO only if penalty changed!
            from runner.models import Submission

            course_submissions = Submission.objects.filter(
                exercise__session__course=self
            )
            for submission in course_submissions:
                submission.refresh_grade()

        super(Course, self).save(*args, **kwargs)

    def make_auto_groups(self):
        """
        Create groups of students, ordered alphabetically by username.
        """

        # Get groups
        student_groups = StudentGroup.objects.filter(course=self).order_by("name")

        # Empty groups
        for group in student_groups:
            group.students.clear()

        # Get students
        students = list(self.students.all().order_by("username"))
        number_of_groups = StudentGroup.objects.filter(course=self).count()

        # Evenly distribute students into groups
        group_repartition = [
            len(students) // number_of_groups
            + (1 if x < len(students) % number_of_groups else 0)
            for x in range(number_of_groups)
        ]

        # Put students into groups according to repartition
        for i in range(number_of_groups):
            for _ in range(group_repartition[i]):
                student_groups[i].students.add(students.pop(0))

        # Save groups
        for group in student_groups:
            group.save()


class StudentGroup(models.Model):
    """
    A group of students, related to one course.
    """

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    students = models.ManyToManyField(
        User, related_name="%(class)s_students", blank=True
    )

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        super(StudentGroup, self).save(*args, **kwargs)

        if is_new:
            self.course.handle_student_groups_change()

    def delete(self, *args, **kwargs):
        result = super(StudentGroup, self).delete(*args, **kwargs)
        self.course.handle_student_groups_change()
        return result

    def __str__(self):
        return f"{self.name} ({self.course.title})"


class Session(models.Model):
    """
    A part of a course, that includes exercises
    """

    class DeadlineTypes(models.TextChoices):
        SOFT = "soft", _("Soft")
        HARD = "hard", _("Hard")

    id: int
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    grade = models.FloatField(blank=True, null=True)

    start_date = models.DateTimeField(blank=True, null=True)

    deadline_type = models.CharField(
        max_length=4,
        choices=DeadlineTypes.choices,
        default=DeadlineTypes.SOFT,
    )
    deadline = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.course.title + " : " + self.title

    def save(self, *args, **kwargs):
        super(Session, self).save(*args, **kwargs)

        if self.pk is not None:
            # Get submissions related to this session
            # And update their grades
            # TODO only if session grade or deadline changed!
            from runner.models import Submission

            session_submissions = Submission.objects.filter(exercise__session=self)
            for submission in session_submissions:
                submission.refresh_grade()


class Exercise(models.Model):
    """
    The exercise given to the student
    """

    class ExerciseTypes(models.TextChoices):
        SINGLE = "single", _("Single")
        MULTIPLE = "multiple", _("Multiple")

    id: int
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=8,
        choices=ExerciseTypes.choices,
        default=ExerciseTypes.SINGLE,
    )
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    grade = models.FloatField(blank=True, null=True)

    # Single-file exercises specifics
    prefix = models.TextField(blank=True)
    suffix = models.TextField(blank=True)

    # Multiple-file exercises specifics
    teacher_files = models.FileField(upload_to="teacher_files/", blank=True, null=True)

    def __str__(self):
        if self.type == self.ExerciseTypes.MULTIPLE:
            return self.title + " (multiple-file)"
        else:
            return self.title
