# Generated by Django 4.1.2 on 2022-11-21 10:01

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("api", "0003_alter_course_students"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="course",
            name="owner",
        ),
        migrations.AddField(
            model_name="course",
            name="owners",
            field=models.ManyToManyField(
                related_name="%(class)s_courses_owners", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
