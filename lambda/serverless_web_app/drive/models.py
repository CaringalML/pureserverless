from django.db import models


class DriveFolder(models.Model):
    owner_sub  = models.CharField(max_length=128, db_index=True)
    name       = models.CharField(max_length=255)
    parent     = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE, related_name='subfolders',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = [('owner_sub', 'parent', 'name')]

    def __str__(self):
        return self.name


class DriveFile(models.Model):
    STANDARD      = "STANDARD"
    STANDARD_IA   = "STANDARD_IA"
    GLACIER_IR    = "GLACIER_IR"
    GLACIER       = "GLACIER"
    DEEP_ARCHIVE  = "DEEP_ARCHIVE"

    STORAGE_CLASS_CHOICES = [
        (STANDARD,     "Standard"),
        (STANDARD_IA,  "Standard-IA"),
        (GLACIER_IR,   "Glacier Instant Retrieval"),
        (GLACIER,      "Glacier Flexible Retrieval"),
        (DEEP_ARCHIVE, "Deep Archive"),
    ]

    # Cognito user sub — ties file to owner without a users table
    owner_sub    = models.CharField(max_length=128, db_index=True)
    folder       = models.ForeignKey(
        DriveFolder, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='files',
    )
    name         = models.CharField(max_length=255)
    s3_key       = models.CharField(max_length=512, unique=True)
    size         = models.BigIntegerField(default=0)
    content_type = models.CharField(max_length=100, default="application/octet-stream")
    storage_class = models.CharField(
        max_length=20,
        choices=STORAGE_CLASS_CHOICES,
        default=STANDARD,
    )
    uploaded_at  = models.DateTimeField(auto_now_add=True)

    RESTORE_PENDING = "pending"
    RESTORE_READY   = "ready"
    RESTORE_STATUS_CHOICES = [
        (RESTORE_PENDING, "Restoring"),
        (RESTORE_READY,   "Ready"),
    ]
    restore_status       = models.CharField(max_length=10, blank=True, default="",
                                            choices=RESTORE_STATUS_CHOICES)
    restore_notify_email = models.EmailField(blank=True, default="")

    class Meta:
        ordering = ["-uploaded_at"]

    def size_display(self):
        for unit in ["B", "KB", "MB", "GB"]:
            if self.size < 1024:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024
        return f"{self.size:.1f} TB"

    def is_viewable_inline(self):
        return self.content_type.startswith(("image/", "video/", "audio/", "application/pdf", "text/"))

    def is_archived(self):
        return self.storage_class in (self.GLACIER, self.DEEP_ARCHIVE)
