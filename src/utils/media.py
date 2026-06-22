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

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

PRESIGN_EXPIRY_SECONDS = 900

# Stable, never-expiring marker embedded in body for private images.
# Resolved into a fresh presigned URL on every admin-side read — never
# stored or served to the public read path.
PRIVATE_MARKER_PREFIX = "media-key:"

# LocalStack serves plain http; real CloudFront is always https.
CDN_SCHEME = "http" if os.environ.get("S3_ENDPOINT_URL") else "https"

# Only set locally — swaps the container-internal S3 endpoint for one the
# browser can actually resolve.
_BROWSER_S3_ENDPOINT_URL = os.environ.get("BROWSER_S3_ENDPOINT_URL")


def _public_prefix(domain: str) -> str:
    return f"{domain}-images"


def _private_prefix(domain: str) -> str:
    return f"{domain}-private-images"


def _public_url(key: str) -> str:
    return f"{CDN_SCHEME}://{os.environ['MEDIA_CDN_DOMAIN']}/{key}"


def _marker(key: str) -> str:
    return f"{PRIVATE_MARKER_PREFIX}{key}"


def diff_image_keys(old_images: dict, new_images: dict) -> set[str]:
    return set((old_images or {}).keys()) - set((new_images or {}).keys())


def delete_media_keys(keys: set[str]) -> None:
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


def generate_presigned_upload(filename: str, domain: str = "content") -> dict:
    """New uploads always land under the domain's private prefix;
    promote_to_public is what makes them publicly reachable."""
    extension = _guess_extension(filename)
    date_prefix = datetime.now(timezone.utc).strftime("%Y/%m")
    stub = _safe_filename_stub(filename)
    key = f"{_private_prefix(domain)}/{date_prefix}/{uuid.uuid4().hex}-{stub}.{extension}"

    upload_url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": MEDIA_BUCKET_NAME,
            "Key": key,
            "ContentType": "application/octet-stream",
        },
        ExpiresIn=PRESIGN_EXPIRY_SECONDS,
    )

    if _BROWSER_S3_ENDPOINT_URL:
        internal_endpoint = os.environ.get("S3_ENDPOINT_URL", "")
        upload_url = upload_url.replace(internal_endpoint, _BROWSER_S3_ENDPOINT_URL)

    return {"key": key, "upload_url": upload_url}


def _swap_prefix(key: str, from_prefix: str, to_prefix: str) -> str:
    if key.startswith(from_prefix + "/"):
        return to_prefix + key[len(from_prefix):]
    return key


def promote_to_public(keys: set[str], domain: str = "content") -> dict[str, str]:
    """Moves keys from the domain's private prefix to its public prefix.
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
            print(f"Failed to promote media key '{key}' to public: {e}")
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
            print(f"Failed to demote media key '{key}' to private: {e}")
    return moved


def generate_presigned_read(key: str) -> str:
    """Lets the admin UI preview a private image — the public CDN has
    no route to any *-private-images prefix."""
    url = s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": MEDIA_BUCKET_NAME, "Key": key},
        ExpiresIn=PRESIGN_EXPIRY_SECONDS,
    )
    if _BROWSER_S3_ENDPOINT_URL:
        internal_endpoint = os.environ.get("S3_ENDPOINT_URL", "")
        url = url.replace(internal_endpoint, _BROWSER_S3_ENDPOINT_URL)
    return url


def resolve_pending_images(images: dict, domain: str = "content") -> tuple[dict, dict, dict]:
    """New images land in the private prefix. body_replacements gets a
    stable marker (never expires) rather than a live presigned URL —
    the marker is resolved into a real URL on each admin read instead,
    see resolve_body_markers_for_display."""
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


def rewrite_body_for_moved_images(body: str, moved: dict[str, str], domain: str = "content") -> str:
    """Promoted keys get the real CDN URL (permanent). Demoted keys get
    a marker (resolved fresh on each admin read).

    Promoted: replace marker (media-key:old_key) -> real CDN URL
    Demoted:  replace real CDN URL (old_key was public) -> marker"""
    public_prefix = _public_prefix(domain)
    replacements: dict[str, str] = {}
    for old_key, new_key in moved.items():
        if new_key.startswith(public_prefix + "/"):
            # Promoting: old was private (stored as marker), new is public
            replacements[_marker(old_key)] = _public_url(new_key)
        else:
            # Demoting: old was public (stored as real CDN URL), new is private
            replacements[_public_url(old_key)] = _marker(new_key)
    return apply_body_replacements(body, replacements)


def resolve_body_markers_for_display(body: str) -> str:
    """Admin-read-only step: finds every media-key: marker in body and
    swaps it for a freshly-generated presigned URL. Never called on the
    public read path — public posts only ever contain real CDN URLs,
    never markers, since only published (public) content is publicly
    readable in the first place."""
    if PRIVATE_MARKER_PREFIX not in body:
        return body

    pattern = re.compile(re.escape(PRIVATE_MARKER_PREFIX) + r'([^"\'\s)]+)')

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        return generate_presigned_read(key)

    return pattern.sub(_replace, body)


_PRIVATE_KEY_IN_URL = re.compile(
    r"https?://[^\s\"'?]+/((?:[a-zA-Z0-9_-]+-private-images)/[^\s\"'?]+)\?[^\s\"']*"
)


def normalize_body_to_markers(body: str) -> str:
    """The inverse of resolve_body_markers_for_display, run on every
    save. The editor's live DOM may contain real presigned URLs for
    private images (resolved earlier so they could be displayed) —
    those must never be persisted as-is, since they expire. Any such
    URL found in the incoming body is converted back to its stable
    media-key: marker before writing to the database."""
    def _replace(match: re.Match) -> str:
        key = match.group(1)
        return _marker(key)

    return _PRIVATE_KEY_IN_URL.sub(_replace, body)


_PUBLIC_KEY_IN_URL = re.compile(
    r"https?://[^\s\"'?]+/((?:[a-zA-Z0-9_-]+-images)/[^\s\"'?]+)"
)


def extract_image_keys_from_body(body: str) -> set[str]:
    """The source of truth for 'which images does this post currently
    reference' — derived from body itself rather than trusted from the
    frontend's images payload, so a stale or buggy client can't cause
    an in-use image to look orphaned (or a removed one to look kept).

    Call this *after* normalize_body_to_markers, so any private image
    is already a media-key: marker, not a raw URL — the public-URL
    pattern below then only ever matches genuinely public CDN links."""
    keys: set[str] = set()
    keys.update(re.findall(
        re.escape(PRIVATE_MARKER_PREFIX) + r'([^"\'\s)]+)', body
    ))
    keys.update(m.group(1) for m in _PUBLIC_KEY_IN_URL.finditer(body))
    return keys