# Generated by Django 4.1.4 on 2023-07-22 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0016_remove_course_auto_groups_number_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course",
            name="groups_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
