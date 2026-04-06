from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('drive', '0008_batchjob_progress')]
    operations = [
        migrations.AddField(
            model_name='drivefolder',
            name='deleted_at',
            field=models.DateTimeField(null=True, blank=True, db_index=True),
        ),
    ]
