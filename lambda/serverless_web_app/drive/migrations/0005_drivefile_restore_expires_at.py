from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drive', '0004_drivefile_deleted_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='drivefile',
            name='restore_expires_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
