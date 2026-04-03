import datetime
import json
import uuid
from urllib.parse import quote

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
from .models import DriveFile, DriveFolder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _s3():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        endpoint_url=f"https://s3.{settings.AWS_REGION}.amazonaws.com",
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
    # URL-encode the path (spaces → %20 etc.) so the signature matches what
    # the browser actually requests. safe='/' preserves path separators.
    encoded_key = quote(s3_key, safe="/")
    url = f"https://{settings.CLOUDFRONT_DOMAIN}/{encoded_key}"
    expire_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_seconds)
    return cf_signer.generate_presigned_url(url, date_less_than=expire_at)


def _build_breadcrumbs(folder):
    """Walk up the parent chain and return [root, ..., folder]."""
    crumbs = []
    node = folder
    while node:
        crumbs.insert(0, node)
        node = node.parent
    return crumbs


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@cognito_login_required
def drive_home(request, folder_pk=None):
    owner_sub = _get_owner_sub(request)

    current_folder = None
    breadcrumbs = []
    if folder_pk:
        current_folder = get_object_or_404(DriveFolder, pk=folder_pk, owner_sub=owner_sub)
        breadcrumbs = _build_breadcrumbs(current_folder)

    files = DriveFile.objects.filter(owner_sub=owner_sub, folder=current_folder)
    subfolders = DriveFolder.objects.filter(owner_sub=owner_sub, parent=current_folder)

    # Sidebar: top-level folders with one level of children pre-fetched
    sidebar_folders = DriveFolder.objects.filter(
        owner_sub=owner_sub, parent=None
    ).prefetch_related('subfolders')

    return render(request, "drive/home.html", {
        "files": files,
        "subfolders": subfolders,
        "current_folder": current_folder,
        "breadcrumbs": breadcrumbs,
        "sidebar_folders": sidebar_folders,
    })


@cognito_login_required
@require_POST
def create_folder(request):
    """Create a new folder and return its rendered row HTML."""
    try:
        data = json.loads(request.body)
        name = data.get("name", "").strip()
        parent_pk = data.get("parent_pk")
        owner_sub = _get_owner_sub(request)

        if not name:
            return JsonResponse({"error": "Folder name is required"}, status=400)

        parent = None
        if parent_pk:
            parent = get_object_or_404(DriveFolder, pk=parent_pk, owner_sub=owner_sub)

        folder = DriveFolder.objects.create(
            owner_sub=owner_sub,
            name=name,
            parent=parent,
        )

        html = render(request, "drive/partials/folder_row.html", {"folder": folder}).content.decode()
        return JsonResponse({"html": html, "id": folder.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@cognito_login_required
@require_POST
def delete_folder(request, pk):
    """Delete a folder (CASCADE removes all sub-folders; files are unlinked via SET_NULL then deleted)."""
    owner_sub = _get_owner_sub(request)
    folder = get_object_or_404(DriveFolder, pk=pk, owner_sub=owner_sub)

    # Delete all files inside the folder (and subfolders) from S3
    all_files = DriveFile.objects.filter(owner_sub=owner_sub, s3_key__startswith=f"{owner_sub}/")
    # Narrow to files that belong to this folder subtree via the DB
    def _collect_folder_ids(f, ids=None):
        if ids is None:
            ids = []
        ids.append(f.pk)
        for child in f.subfolders.all():
            _collect_folder_ids(child, ids)
        return ids

    folder_ids = _collect_folder_ids(folder)
    files_to_delete = DriveFile.objects.filter(owner_sub=owner_sub, folder_id__in=folder_ids)
    s3 = _s3()
    for f in files_to_delete:
        try:
            s3.delete_object(Bucket=settings.DRIVE_BUCKET_NAME, Key=f.s3_key)
        except ClientError:
            pass

    folder.delete()  # CASCADE handles sub-folders in DB
    return HttpResponse("")


@cognito_login_required
@require_POST
def upload_url(request):
    """Return a presigned S3 POST URL — the browser uploads directly to S3."""
    try:
        if not settings.DRIVE_BUCKET_NAME:
            return JsonResponse({"error": "DRIVE_BUCKET_NAME env var not set — has Terraform been applied?"}, status=500)

        data = json.loads(request.body)
        filename     = data.get("filename", "unnamed")
        content_type = data.get("content_type", "application/octet-stream")
        owner_sub    = _get_owner_sub(request)

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
        folder_pk = data.get("folder_pk")

        folder = None
        if folder_pk:
            folder = get_object_or_404(DriveFolder, pk=folder_pk, owner_sub=owner_sub)

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
            folder=folder,
        )

        html = render(request, "drive/partials/file_row.html", {"file": drive_file}).content.decode()
        return JsonResponse({"html": html, "id": drive_file.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@cognito_login_required
def download_file(request, pk):
    """Redirect to a presigned S3 GET URL with Content-Disposition: attachment."""
    file = get_object_or_404(DriveFile, pk=pk, owner_sub=_get_owner_sub(request))
    if file.is_archived():
        return HttpResponse("This file is archived and cannot be downloaded directly.", status=400)

    presigned_url = _s3().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.DRIVE_BUCKET_NAME,
            "Key": file.s3_key,
            "ResponseContentDisposition": f'attachment; filename="{quote(file.name)}"',
            "ResponseContentType": file.content_type,
        },
        ExpiresIn=300,
    )
    return redirect(presigned_url)


@cognito_login_required
def get_file_url(request, pk):
    """Return a signed CloudFront URL as JSON for the in-browser preview modal."""
    file = get_object_or_404(DriveFile, pk=pk, owner_sub=_get_owner_sub(request))
    if file.is_archived():
        return JsonResponse(
            {"error": "archived", "message": "This file is archived and cannot be previewed."},
            status=400,
        )
    signed_url = _get_cloudfront_signed_url(file.s3_key, expires_seconds=3600)
    return JsonResponse({
        "url": signed_url,
        "content_type": file.content_type,
        "name": file.name,
        "size": file.size_display(),
    })


@cognito_login_required
def view_file(request, pk):
    """Redirect to a short-lived CloudFront signed URL (fallback / direct link)."""
    file = get_object_or_404(DriveFile, pk=pk, owner_sub=_get_owner_sub(request))

    if file.is_archived():
        return render(request, "drive/archived.html", {"file": file})

    signed_url = _get_cloudfront_signed_url(file.s3_key, expires_seconds=3600)
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
        file_ids     = data.get("ids", [])
        target_class = data.get("storage_class", "GLACIER")
        owner_sub    = _get_owner_sub(request)

        if target_class not in ("GLACIER", "DEEP_ARCHIVE"):
            return JsonResponse({"error": "Invalid storage class"}, status=400)

        files = DriveFile.objects.filter(id__in=file_ids, owner_sub=owner_sub)
        updated_html = []

        for f in files:
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
