from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drive', '0005_drivefile_restore_expires_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drivefile',
            name='storage_class',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('STANDARD',     'Standard'),
                    ('STANDARD_IA',  'Standard-IA'),
                    ('GLACIER_IR',   'Glacier Instant Retrieval'),
                    ('GLACIER',      'Glacier Flexible Retrieval'),
                    ('DEEP_ARCHIVE', 'Deep Archive'),
                ],
                default='GLACIER_IR',
            ),
        ),
    ]
