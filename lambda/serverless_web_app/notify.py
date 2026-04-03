"""
Lambda handler for S3 ObjectRestore:Completed events.

Triggered by S3 → Lambda notification when a Glacier restore finishes.
Looks up the file in the DB, sends a "ready to download" email via Resend,
and updates the restore_status to 'ready'.
"""
import json
import os
from urllib.parse import unquote_plus

import boto3
import psycopg2
import resend
from urllib.parse import urlparse


def handler(event, context):
    for record in event.get("Records", []):
        event_name = record.get("eventName", "")
        if "ObjectRestore:Completed" not in event_name:
            continue

        s3_key = unquote_plus(record["s3"]["object"]["key"])
        _handle_restore_completed(s3_key)


def _handle_restore_completed(s3_key):
    region      = os.environ.get("AWS_REGION", "ap-southeast-2")
    ssm         = boto3.client("ssm", region_name=region)

    db_url = ssm.get_parameter(
        Name=os.environ["SSM_DATABASE_URL_NAME"], WithDecryption=True
    )["Parameter"]["Value"]

    resend_key = ssm.get_parameter(
        Name=os.environ["SSM_RESEND_API_KEY_NAME"], WithDecryption=True
    )["Parameter"]["Value"]

    parsed   = urlparse(db_url)
    conn     = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        sslmode="require",
    )

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, restore_notify_email FROM drive_drivefile WHERE s3_key = %s",
                    (s3_key,),
                )
                row = cur.fetchone()
                if not row:
                    return

                file_id, file_name, notify_email = row

                cur.execute(
                    "UPDATE drive_drivefile SET restore_status = 'ready' WHERE id = %s",
                    (file_id,),
                )
    finally:
        conn.close()

    if not notify_email:
        return

    resend.api_key = resend_key
    from_email     = os.environ.get("DRIVE_FROM_EMAIL", "noreply@nodepulsecaringal.xyz")

    resend.Emails.send({
        "from": from_email,
        "to": [notify_email],
        "subject": f'StrawDrive: "{file_name}" is ready to download',
        "html": _build_ready_email(file_name),
    })


def _build_ready_email(file_name):
    drive_url = os.environ.get("DRIVE_URL", "https://drive.nodepulsecaringal.xyz/drive/")
    return f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;background:#0f172a;padding:32px;border-radius:12px;">
        <div style="text-align:center;margin-bottom:24px;">
            <div style="display:inline-flex;align-items:center;justify-content:center;
                        width:56px;height:56px;background:#14532d;border-radius:50%;margin-bottom:12px;">
                <span style="font-size:28px;">&#10003;</span>
            </div>
            <h2 style="color:#f1f5f9;margin:0;">Your file is ready!</h2>
        </div>

        <p style="color:#94a3b8;text-align:center;">
            Your Glacier Deep Archive restore has completed successfully.
        </p>

        <div style="background:#1e293b;border-radius:8px;padding:16px;margin:20px 0;
                    border-left:4px solid #22c55e;display:flex;align-items:center;gap:12px;">
            <span style="font-size:24px;">&#128196;</span>
            <p style="color:#e2e8f0;margin:0;font-weight:600;">{file_name}</p>
        </div>

        <div style="text-align:center;margin:28px 0;">
            <a href="{drive_url}"
               style="display:inline-block;background:#0ea5e9;color:#fff;text-decoration:none;
                      font-weight:600;padding:12px 28px;border-radius:8px;font-size:15px;">
                Go to StrawDrive &rarr;
            </a>
        </div>

        <div style="background:#172554;border:1px solid #1e3a8a;border-radius:8px;padding:12px 16px;margin:20px 0;">
            <p style="color:#93c5fd;font-size:13px;margin:0;">
                &#9432;&nbsp; The restored copy is available for <strong>7 days</strong>.
                After that it will return to Deep Archive automatically.
            </p>
        </div>

        <hr style="border:none;border-top:1px solid #1e293b;margin:24px 0;">
        <p style="color:#475569;font-size:12px;margin:0;text-align:center;">
            StrawDrive &nbsp;·&nbsp; nodepulsecaringal.xyz
        </p>
    </div>
    """
