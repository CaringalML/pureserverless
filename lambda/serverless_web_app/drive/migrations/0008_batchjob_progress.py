from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drive', '0007_batchjob'),
    ]

    operations = [
        migrations.AddField(
            model_name='batchjob',
            name='progress',
            field=models.IntegerField(default=0),
        ),
    ]
