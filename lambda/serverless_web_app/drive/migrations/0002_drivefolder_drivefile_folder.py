import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drive", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DriveFolder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("owner_sub", models.CharField(db_index=True, max_length=128)),
                ("name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("parent", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="subfolders",
                    to="drive.drivefolder",
                )),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="drivefolder",
            unique_together={("owner_sub", "parent", "name")},
        ),
        migrations.AddField(
            model_name="drivefile",
            name="folder",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="files",
                to="drive.drivefolder",
            ),
        ),
    ]
