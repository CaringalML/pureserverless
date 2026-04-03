from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drive", "0002_drivefolder_drivefile_folder"),
    ]

    operations = [
        migrations.AddField(
            model_name="drivefile",
            name="restore_status",
            field=models.CharField(
                blank=True,
                choices=[("pending", "Restoring"), ("ready", "Ready")],
                default="",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="drivefile",
            name="restore_notify_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
    ]
