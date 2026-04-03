import datetime
import json
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts.decorators import cognito_login_required
from .models import DriveFile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _s3():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        config=Config(signature_version="s3v4"),
    )


def _get_owner_sub(request):
    """Return the Cognito sub stored in the session."""
    return request.session.get("user_sub", "")


def _get_cloudfront_signed_url(s3_key, expires_seconds=300):
    """Generate a CloudFront signed URL valid for expires_seconds."""
    ssm = boto3.client("ssm", region_name=settings.AWS_REGION)
    pem = ssm.get_parameter(
        Name=settings.CLOUDFRONT_PRIVATE_KEY_SSM_NAME,
        WithDecryption=True,
    )["Parameter"]["Value"]

    private_key = serialization.load_pem_private_key(pem.encode(), password=None)

    def rsa_signer(message):
        return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())

    cf_signer = CloudFrontSigner(settings.CLOUDFRONT_KEY_PAIR_ID, rsa_signer)
    url = f"https://{settings.CLOUDFRONT_DOMAIN}/{s3_key}"
    expire_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_seconds)
    return cf_signer.generate_presigned_url(url, date_less_than=expire_at)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@cognito_login_required
def drive_home(request):
    owner_sub = _get_owner_sub(request)
    files = DriveFile.objects.filter(owner_sub=owner_sub)
    return render(request, "drive/home.html", {"files": files})


@cognito_login_required
@require_POST
def upload_url(request):
    """Return a presigned S3 POST URL — the browser uploads directly to S3."""
    try:
        if not settings.DRIVE_BUCKET_NAME:
            return JsonResponse({"error": "DRIVE_BUCKET_NAME env var not set — has Terraform been applied?"}, status=500)

        data = json.loads(request.body)
        filename    = data.get("filename", "unnamed")
        content_type = data.get("content_type", "application/octet-stream")
        owner_sub   = _get_owner_sub(request)

        s3_key = f"{owner_sub}/{uuid.uuid4()}/{filename}"

        presigned = _s3().generate_presigned_post(
            Bucket=settings.DRIVE_BUCKET_NAME,
            Key=s3_key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, 500 * 1024 * 1024],  # max 500 MB
            ],
            ExpiresIn=300,
        )
        return JsonResponse({"url": presigned["url"], "fields": presigned["fields"], "s3_key": s3_key})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@cognito_login_required
@require_POST
def confirm_upload(request):
    """Save file metadata after successful S3 upload."""
    try:
        data = json.loads(request.body)
        owner_sub = _get_owner_sub(request)

        # Verify the object actually exists in S3
        head = _s3().head_object(
            Bucket=settings.DRIVE_BUCKET_NAME,
            Key=data["s3_key"],
        )

        drive_file = DriveFile.objects.create(
            owner_sub=owner_sub,
            name=data["filename"],
            s3_key=data["s3_key"],
            size=head["ContentLength"],
            content_type=head.get("ContentType", "application/octet-stream"),
        )

        html = render(request, "drive/partials/file_row.html", {"file": drive_file}).content.decode()
        return JsonResponse({"html": html, "id": drive_file.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@cognito_login_required
def view_file(request, pk):
    """Redirect to a short-lived CloudFront signed URL."""
    file = get_object_or_404(DriveFile, pk=pk, owner_sub=_get_owner_sub(request))

    if file.is_archived():
        return render(request, "drive/archived.html", {"file": file})

    signed_url = _get_cloudfront_signed_url(file.s3_key, expires_seconds=300)
    return redirect(signed_url)


@cognito_login_required
@require_POST
def delete_file(request, pk):
    """Delete from S3 and DB, return empty response so HTMX removes the row."""
    file = get_object_or_404(DriveFile, pk=pk, owner_sub=_get_owner_sub(request))
    try:
        _s3().delete_object(Bucket=settings.DRIVE_BUCKET_NAME, Key=file.s3_key)
    except ClientError:
        pass
    file.delete()
    return HttpResponse("")


@cognito_login_required
@require_POST
def archive_files(request):
    """Move selected files to Glacier Flexible or Deep Archive immediately."""
    try:
        data = json.loads(request.body)
        file_ids      = data.get("ids", [])
        target_class  = data.get("storage_class", "GLACIER")  # GLACIER or DEEP_ARCHIVE
        owner_sub     = _get_owner_sub(request)

        if target_class not in ("GLACIER", "DEEP_ARCHIVE"):
            return JsonResponse({"error": "Invalid storage class"}, status=400)

        files = DriveFile.objects.filter(id__in=file_ids, owner_sub=owner_sub)
        updated_html = []

        for f in files:
            # S3 copy-in-place to change storage class immediately
            _s3().copy_object(
                Bucket=settings.DRIVE_BUCKET_NAME,
                CopySource={"Bucket": settings.DRIVE_BUCKET_NAME, "Key": f.s3_key},
                Key=f.s3_key,
                StorageClass=target_class,
                MetadataDirective="COPY",
            )
            f.storage_class = target_class
            f.save(update_fields=["storage_class"])
            html = render(request, "drive/partials/file_row.html", {"file": f}).content.decode()
            updated_html.append({"id": f.id, "html": html})

        return JsonResponse({"updated": updated_html})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
