import os
import re
import uuid
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

s3_client = boto3.client(
    "s3",
    endpoint_url=os.environ.get("S3_ENDPOINT_URL") or None,
    region_name=os.environ.get("AWS_REGION", "ap-southeast-1"),
)

MEDIA_BUCKET_NAME = os.environ["MEDIA_BUCKET_NAME"]

PRESIGN_EXPIRY_SECONDS = 900

# Stable marker embedded in body for private images. Resolved into a
# fresh presigned URL on every admin read, never stored as a real URL.
PRIVATE_MARKER_PREFIX = "media-key:"

# LocalStack serves plain http; real CloudFront is always https.
CDN_SCHEME = "http" if os.environ.get("S3_ENDPOINT_URL") else "https"

# Only set locally — swaps the container-internal S3 endpoint for one
# the browser can actually resolve.
_BROWSER_S3_ENDPOINT_URL = os.environ.get("BROWSER_S3_ENDPOINT_URL")

_KNOWN_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

_PRIVATE_KEY_IN_URL = re.compile(
    r"https?://[^\s\"'?]+/((?:[a-zA-Z0-9_-]+-private-images)/[^\s\"'?]+)\?[^\s\"']*"
)

_PUBLIC_KEY_IN_URL = re.compile(
    r"https?://[^\s\"'?]+/((?:[a-zA-Z0-9_-]+-images)/[^\s\"'?]+)"
)


def _public_prefix(domain: str) -> str:
    return f"{domain}-images"


def _private_prefix(domain: str) -> str:
    return f"{domain}-private-images"


def _public_url(key: str) -> str:
    return f"{CDN_SCHEME}://{os.environ['MEDIA_CDN_DOMAIN']}/{key}"


def _marker(key: str) -> str:
    return f"{PRIVATE_MARKER_PREFIX}{key}"


def _swap_prefix(key: str, from_prefix: str, to_prefix: str) -> str:
    if key.startswith(from_prefix + "/"):
        return to_prefix + key[len(from_prefix):]
    return key


def _safe_filename_stub(original_filename: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_-]", "-", original_filename.rsplit(".", 1)[0])
    return name[:50].strip("-") or "image"


def _guess_extension(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext if ext in _KNOWN_EXTENSIONS else "jpg"


def _apply_browser_endpoint(url: str) -> str:
    if _BROWSER_S3_ENDPOINT_URL:
        internal = os.environ.get("S3_ENDPOINT_URL", "")
        return url.replace(internal, _BROWSER_S3_ENDPOINT_URL)
    return url


def diff_image_keys(old_images: dict, new_images: dict) -> set[str]:
    return set((old_images or {}).keys()) - set((new_images or {}).keys())


def delete_media_keys(keys: set[str]) -> None:
    for key in keys:
        try:
            s3_client.delete_object(Bucket=MEDIA_BUCKET_NAME, Key=key)
        except ClientError as e:
            print(f"Failed to delete media key '{key}': {e}")


def generate_presigned_upload(filename: str, domain: str = "content") -> dict:
    """New uploads always land under the private prefix; promote_to_public
    is what makes them publicly reachable."""
    extension = _guess_extension(filename)
    date_prefix = datetime.now(timezone.utc).strftime("%Y/%m")
    stub = _safe_filename_stub(filename)
    key = f"{_private_prefix(domain)}/{date_prefix}/{uuid.uuid4().hex}-{stub}.{extension}"

    upload_url = _apply_browser_endpoint(
        s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": MEDIA_BUCKET_NAME,
                "Key": key,
                "ContentType": "application/octet-stream",
            },
            ExpiresIn=PRESIGN_EXPIRY_SECONDS,
        )
    )
    return {"key": key, "upload_url": upload_url}


def generate_presigned_read(key: str) -> str:
    """Short-lived read URL for admin preview of private images.
    The public CDN has no route to any *-private-images prefix."""
    return _apply_browser_endpoint(
        s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": MEDIA_BUCKET_NAME, "Key": key},
            ExpiresIn=PRESIGN_EXPIRY_SECONDS,
        )
    )


def promote_to_public(keys: set[str], domain: str = "content") -> dict[str, str]:
    """Moves keys from the private prefix to the public prefix.
    Returns {old_key: new_key} for keys actually moved."""
    private_prefix = _private_prefix(domain)
    public_prefix = _public_prefix(domain)
    moved: dict[str, str] = {}
    for key in keys:
        if not key.startswith(private_prefix + "/"):
            continue
        new_key = _swap_prefix(key, private_prefix, public_prefix)
        try:
            s3_client.copy_object(
                Bucket=MEDIA_BUCKET_NAME,
                CopySource={"Bucket": MEDIA_BUCKET_NAME, "Key": key},
                Key=new_key,
            )
            s3_client.delete_object(Bucket=MEDIA_BUCKET_NAME, Key=key)
            moved[key] = new_key
        except ClientError as e:
            print(f"Failed to promote '{key}': {e}")
    return moved


def demote_to_private(keys: set[str], domain: str = "content") -> dict[str, str]:
    """Inverse of promote_to_public."""
    public_prefix = _public_prefix(domain)
    private_prefix = _private_prefix(domain)
    moved: dict[str, str] = {}
    for key in keys:
        if not key.startswith(public_prefix + "/"):
            continue
        new_key = _swap_prefix(key, public_prefix, private_prefix)
        try:
            s3_client.copy_object(
                Bucket=MEDIA_BUCKET_NAME,
                CopySource={"Bucket": MEDIA_BUCKET_NAME, "Key": key},
                Key=new_key,
            )
            s3_client.delete_object(Bucket=MEDIA_BUCKET_NAME, Key=key)
            moved[key] = new_key
        except ClientError as e:
            print(f"Failed to demote '{key}': {e}")
    return moved


def resolve_pending_images(images: dict, domain: str = "content") -> tuple[dict, dict, dict]:
    clean_images: dict = {}
    upload_urls: dict = {}
    body_replacements: dict = {}

    for blob_key, meta in (images or {}).items():
        if isinstance(meta, dict) and "filename" in meta:
            presigned = generate_presigned_upload(meta["filename"], domain=domain)
            display_url = generate_presigned_read(presigned["key"])
            clean_images[presigned["key"]] = {}
            upload_urls[blob_key] = {**presigned, "display_url": display_url}
            body_replacements[blob_key] = _marker(presigned["key"])
        else:
            clean_images[blob_key] = meta

    return clean_images, upload_urls, body_replacements


def apply_body_replacements(body: str, replacements: dict) -> str:
    for old, new in replacements.items():
        body = body.replace(old, new)
    return body


def normalize_body_to_markers(body: str) -> str:
    """Converts any live presigned URLs for private images back to stable
    markers before saving — the editor may have had real URLs injected
    for display, but those must never be persisted since they expire."""
    return _PRIVATE_KEY_IN_URL.sub(lambda m: _marker(m.group(1)), body)


def resolve_body_markers_for_display(body: str) -> str:
    """Admin-read only: swaps every media-key: marker for a fresh presigned
    URL so the editor can display private images."""
    if PRIVATE_MARKER_PREFIX not in body:
        return body
    pattern = re.compile(re.escape(PRIVATE_MARKER_PREFIX) + r'([^"\'\s)]+)')
    return pattern.sub(lambda m: generate_presigned_read(m.group(1)), body)


def rewrite_body_for_moved_images(body: str, moved: dict[str, str], domain: str = "content") -> str:
    """After a promote/demote, rewrites body URLs to match the new key locations.
    Promoted: media-key:old -> real CDN URL
    Demoted:  real CDN URL -> media-key:new"""
    public_prefix = _public_prefix(domain)
    replacements: dict[str, str] = {}
    for old_key, new_key in moved.items():
        if new_key.startswith(public_prefix + "/"):
            replacements[_marker(old_key)] = _public_url(new_key)
        else:
            replacements[_public_url(old_key)] = _marker(new_key)
    return apply_body_replacements(body, replacements)


def extract_image_keys_from_body(body: str) -> set[str]:
    """Derives the current set of image keys directly from body content.
    Call after normalize_body_to_markers so private images are already
    markers, not raw URLs."""
    keys: set[str] = set()
    keys.update(re.findall(
        re.escape(PRIVATE_MARKER_PREFIX) + r'([^"\'\s)]+)', body
    ))
    keys.update(m.group(1) for m in _PUBLIC_KEY_IN_URL.finditer(body))
    return keys