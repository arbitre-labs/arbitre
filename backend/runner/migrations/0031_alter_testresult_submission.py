# Generated by Django 4.2.7 on 2023-12-06 15:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("runner", "0030_alter_testresult_submission"),
    ]

    operations = [
        migrations.AlterField(
            model_name="testresult",
            name="submission",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="runner.submission"
            ),
        ),
    ]
