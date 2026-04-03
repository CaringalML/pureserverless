from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DriveFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("owner_sub", models.CharField(db_index=True, max_length=128)),
                ("name", models.CharField(max_length=255)),
                ("s3_key", models.CharField(max_length=512, unique=True)),
                ("size", models.BigIntegerField(default=0)),
                ("content_type", models.CharField(default="application/octet-stream", max_length=100)),
                ("storage_class", models.CharField(
                    choices=[
                        ("STANDARD", "Standard"),
                        ("STANDARD_IA", "Standard-IA"),
                        ("GLACIER_IR", "Glacier Instant Retrieval"),
                        ("GLACIER", "Glacier Flexible Retrieval"),
                        ("DEEP_ARCHIVE", "Deep Archive"),
                    ],
                    default="STANDARD",
                    max_length=20,
                )),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-uploaded_at"],
            },
        ),
    ]
