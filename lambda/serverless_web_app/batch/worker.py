"""
NovaDrive Batch Worker
Runs inside a Fargate container submitted by AWS Batch.

Required env vars:
  JOB_TYPE              zip_folder
  FOLDER_ID             DriveFolder pk
  OWNER_SUB             Cognito user sub
  JOB_DB_ID             BatchJob pk
  DRIVE_BUCKET_NAME     S3 bucket
  AWS_REGION            e.g. ap-southeast-2
  SSM_DATABASE_URL_NAME SSM parameter name for Neon connection string
"""

import datetime
import io
import logging
import os
import sys
import uuid
import zipfile

import boto3

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _fetch_db_url():
    """Fetch Neon connection string from SSM (same pattern as Lambda)."""
    if url := os.environ.get("DATABASE_URL"):
        return url
    param_name = os.environ.get("SSM_DATABASE_URL_NAME")
    if param_name:
        ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION", "ap-southeast-2"))
        return ssm.get_parameter(Name=param_name, WithDecryption=True)["Parameter"]["Value"]
    raise RuntimeError("No DATABASE_URL or SSM_DATABASE_URL_NAME set")


def _setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
    os.environ["DATABASE_URL"] = _fetch_db_url()
    # Minimal settings overrides so Django doesn't complain about missing vars
    os.environ.setdefault("DJANGO_SECRET_KEY", "batch-worker-placeholder")
    os.environ.setdefault("ALLOWED_HOSTS", "*")

    import django
    django.setup()


def _collect_files(folder_pk, owner_sub):
    """Return list of (DriveFile, arc_path) for all accessible files in the tree."""
    from drive.models import DriveFile, DriveFolder

    accessible = (DriveFile.STANDARD, DriveFile.STANDARD_IA, DriveFile.GLACIER_IR)
    result = []
    queue = [(folder_pk, "")]
    visited = set()

    while queue:
        fk, prefix = queue.pop(0)
        if fk in visited:
            continue
        visited.add(fk)

        for sf in DriveFolder.objects.filter(parent_id=fk, owner_sub=owner_sub):
            child_prefix = f"{prefix}/{sf.name}" if prefix else sf.name
            queue.append((sf.pk, child_prefix))

        for f in DriveFile.objects.filter(
            folder_id=fk, owner_sub=owner_sub,
            deleted_at__isnull=True, storage_class__in=accessible,
        ):
            arc_path = f"{prefix}/{f.name}" if prefix else f.name
            result.append((f, arc_path))

    return result


def run_zip_folder(folder_id, owner_sub, job_db_id):
    from drive.models import DriveFolder, BatchJob

    folder = DriveFolder.objects.filter(pk=folder_id, owner_sub=owner_sub).first()
    if not folder:
        raise RuntimeError(f"Folder {folder_id} not found for owner {owner_sub}")

    files = _collect_files(folder_id, owner_sub)
    log.info("Zipping %d files from folder %s (%s)", len(files), folder_id, folder.name)

    bucket = os.environ["DRIVE_BUCKET_NAME"]
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    s3 = boto3.client("s3", region_name=region)

    # Stream into a BytesIO zip — Fargate has enough memory for large zips
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for drv_file, arc_path in files:
            try:
                obj = s3.get_object(Bucket=bucket, Key=drv_file.s3_key)
                zf.writestr(arc_path, obj["Body"].read())
                log.info("  added %s", arc_path)
            except Exception as e:
                log.warning("  skip %s: %s", drv_file.s3_key, e)

    buf.seek(0)
    zip_key = f"temp-zips/{uuid.uuid4()}.zip"
    s3.put_object(Bucket=bucket, Key=zip_key, Body=buf.getvalue(),
                  ContentType="application/zip")
    log.info("Uploaded zip to s3://%s/%s", bucket, zip_key)

    now = datetime.datetime.now(datetime.timezone.utc)
    BatchJob.objects.filter(pk=job_db_id).update(
        status=BatchJob.READY,
        result_key=zip_key,
        expires_at=now + datetime.timedelta(hours=24),
    )
    log.info("Job %s marked READY", job_db_id)


def main():
    job_type   = os.environ.get("JOB_TYPE", "zip_folder")
    folder_id  = int(os.environ["FOLDER_ID"])
    owner_sub  = os.environ["OWNER_SUB"]
    job_db_id  = int(os.environ["JOB_DB_ID"])

    _setup_django()

    from drive.models import BatchJob
    BatchJob.objects.filter(pk=job_db_id).update(status=BatchJob.RUNNING)

    try:
        if job_type == "zip_folder":
            run_zip_folder(folder_id, owner_sub, job_db_id)
        else:
            raise RuntimeError(f"Unknown JOB_TYPE: {job_type}")
    except Exception as e:
        log.error("Job %s failed: %s", job_db_id, e, exc_info=True)
        from drive.models import BatchJob
        BatchJob.objects.filter(pk=job_db_id).update(status=BatchJob.FAILED)
        sys.exit(1)


if __name__ == "__main__":
    main()
