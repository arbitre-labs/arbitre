# Generated by Django 4.1.1 on 2022-10-03 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0014_remove_test_rules_test_stdin_test_stdout"),
    ]

    operations = [
        migrations.AlterField(
            model_name="testresult",
            name="memory",
            field=models.IntegerField(default=-1),
        ),
        migrations.AlterField(
            model_name="testresult",
            name="time",
            field=models.FloatField(default=-1),
        ),
    ]
