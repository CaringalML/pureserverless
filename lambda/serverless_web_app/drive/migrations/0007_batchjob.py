from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drive', '0006_drivefile_default_glacier_ir'),
    ]

    operations = [
        migrations.CreateModel(
            name='BatchJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_id', models.CharField(blank=True, default='', max_length=128)),
                ('type', models.CharField(default='zip_folder', max_length=32)),
                ('owner_sub', models.CharField(db_index=True, max_length=128)),
                ('folder_name', models.CharField(default='', max_length=255)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('running', 'Running'), ('ready', 'Ready'), ('failed', 'Failed')],
                    default='pending',
                    max_length=16,
                )),
                ('result_key', models.CharField(blank=True, default='', max_length=512)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
