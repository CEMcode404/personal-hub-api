import os
import re
import uuid
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

s3_client = boto3.client(
    "s3",
    endpoint_url=os.environ.get("S3_ENDPOINT_URL") or None,
)

MEDIA_BUCKET_NAME = os.environ["MEDIA_BUCKET_NAME"]

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

PRESIGN_EXPIRY_SECONDS = 300

# LocalStack serves plain http; real CloudFront is always https.
CDN_SCHEME = "http" if os.environ.get("S3_ENDPOINT_URL") else "https"

# The browser cannot resolve host.docker.internal — only containers can.
# S3_ENDPOINT_URL is used to sign the request (must be reachable from
# inside the Lambda container); BROWSER_S3_ENDPOINT_URL, if set, is
# substituted into the final URL the browser will actually PUT to.
_BROWSER_S3_ENDPOINT_URL = os.environ.get("BROWSER_S3_ENDPOINT_URL")


def diff_image_keys(old_images: dict, new_images: dict) -> set[str]:
    """Keys present in old_images but absent from new_images"""
    return set((old_images or {}).keys()) - set((new_images or {}).keys())


def delete_media_keys(keys: set[str]) -> None:
    """Best-effort delete of the given S3 keys. A failed delete is logged,
    not raised"""
    for key in keys:
        try:
            s3_client.delete_object(Bucket=MEDIA_BUCKET_NAME, Key=key)
        except ClientError as e:
            print(f"Failed to delete media key '{key}': {e}")


def _safe_filename_stub(original_filename: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_-]", "-", original_filename.rsplit(".", 1)[0])
    return name[:50].strip("-") or "image"


def _guess_extension(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext if ext in ALLOWED_CONTENT_TYPES.values() else "jpg"


def generate_presigned_upload(filename: str) -> dict:
    """Given an original filename, generates a permanent S3 key and a
    short-lived presigned PUT URL for it. Returns {key, upload_url}."""
    extension = _guess_extension(filename)
    date_prefix = datetime.now(timezone.utc).strftime("%Y/%m")
    stub = _safe_filename_stub(filename)
    key = f"content-images/{date_prefix}/{uuid.uuid4().hex}-{stub}.{extension}"

    upload_url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": MEDIA_BUCKET_NAME, "Key": key},
        ExpiresIn=PRESIGN_EXPIRY_SECONDS,
    )

    if _BROWSER_S3_ENDPOINT_URL:
        internal_endpoint = os.environ.get("S3_ENDPOINT_URL", "")
        upload_url = upload_url.replace(internal_endpoint, _BROWSER_S3_ENDPOINT_URL)

    return {"key": key, "upload_url": upload_url}


def resolve_pending_images(images: dict) -> tuple[dict, dict, dict]:
    """Splits an incoming images dict into (clean_images, upload_urls, body_replacements).

    Entries with a 'filename' are new/pending — their key is the literal
    blob: URL currently sitting in the submitted body's <img src="...">.
    For each, a real S3 key + presigned URL is generated, and:
      - clean_images gets the real key (final, persisted state)
      - upload_urls is keyed by the original blob key, for the frontend
        to know which pending file goes to which presigned URL
      - body_replacements maps blob_url -> real_cdn_url, for substituting
        directly into the submitted body string

    Entries without 'filename' are already-real keys and pass through
    unchanged into clean_images.
    """
    clean_images: dict = {}
    upload_urls: dict = {}
    body_replacements: dict = {}

    for blob_key, meta in (images or {}).items():
        if isinstance(meta, dict) and "filename" in meta:
            presigned = generate_presigned_upload(meta["filename"])
            real_url = f"{CDN_SCHEME}://{os.environ['MEDIA_CDN_DOMAIN']}/{presigned['key']}"
            clean_images[presigned["key"]] = {}
            upload_urls[blob_key] = presigned
            body_replacements[blob_key] = real_url
        else:
            clean_images[blob_key] = meta

    return clean_images, upload_urls, body_replacements


def apply_body_replacements(body: str, replacements: dict) -> str:
    """Substitutes each blob_url -> real_cdn_url mapping directly into
    the body HTML string."""
    for blob_url, real_url in replacements.items():
        body = body.replace(blob_url, real_url)
    return body