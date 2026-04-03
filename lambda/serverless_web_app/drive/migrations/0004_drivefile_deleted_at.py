from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drive", "0003_drivefile_restore_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="drivefile",
            name="deleted_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
