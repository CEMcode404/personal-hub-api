import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from utils import media

class TestDiffImageKeys:

    def test_no_change_returns_empty(self):
        old = {"a.jpg": {}, "b.jpg": {}}
        new = {"a.jpg": {}, "b.jpg": {}}
        assert media.diff_image_keys(old, new) == set()

    def test_removed_key_detected(self):
        old = {"a.jpg": {}, "b.jpg": {}}
        new = {"a.jpg": {}}
        assert media.diff_image_keys(old, new) == {"b.jpg"}

    def test_added_key_not_flagged(self):
        old = {"a.jpg": {}}
        new = {"a.jpg": {}, "b.jpg": {}}
        assert media.diff_image_keys(old, new) == set()

    def test_replaced_key_detected_as_removed(self):
        old = {"a.jpg": {}}
        new = {"b.jpg": {}}
        assert media.diff_image_keys(old, new) == {"a.jpg"}

    def test_old_none_returns_empty(self):
        assert media.diff_image_keys(None, {"a.jpg": {}}) == set()

    def test_new_none_returns_all_old_keys(self):
        assert media.diff_image_keys({"a.jpg": {}, "b.jpg": {}}, None) == {"a.jpg", "b.jpg"}

    def test_both_none_returns_empty(self):
        assert media.diff_image_keys(None, None) == set()

    def test_both_empty_returns_empty(self):
        assert media.diff_image_keys({}, {}) == set()


class TestDeleteMediaKeys:

    def test_deletes_each_key(self):
        with patch.object(media, "s3_client") as mock_s3:
            media.delete_media_keys({"a.jpg", "b.jpg"})
            assert mock_s3.delete_object.call_count == 2
            called_keys = {call.kwargs["Key"] for call in mock_s3.delete_object.call_args_list}
            assert called_keys == {"a.jpg", "b.jpg"}

    def test_empty_set_does_nothing(self):
        with patch.object(media, "s3_client") as mock_s3:
            media.delete_media_keys(set())
            mock_s3.delete_object.assert_not_called()

    def test_failed_delete_does_not_raise(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.delete_object.side_effect = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "DeleteObject"
            )
            media.delete_media_keys({"a.jpg"})

    def test_one_failure_does_not_block_others(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.delete_object.side_effect = [
                ClientError({"Error": {"Code": "AccessDenied", "Message": "denied"}}, "DeleteObject"),
                None,
            ]
            media.delete_media_keys({"a.jpg", "b.jpg"})
            assert mock_s3.delete_object.call_count == 2


# --- generate_presigned_upload ---

class TestGeneratePresignedUpload:

    def test_returns_key_and_upload_url(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://signed-url.example.com"
            result = media.generate_presigned_upload("photo.jpg")
            assert "key" in result
            assert "upload_url" in result
            assert result["upload_url"] == "https://signed-url.example.com"

    def test_key_always_starts_with_private_prefix(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://signed-url.example.com"
            result = media.generate_presigned_upload("photo.jpg")
            assert result["key"].startswith("content-private-images/")

    def test_domain_parameter_changes_prefix(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://signed-url.example.com"
            result = media.generate_presigned_upload("photo.jpg", domain="wiki")
            assert result["key"].startswith("wiki-private-images/")

    def test_key_preserves_known_extension(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://signed-url.example.com"
            result = media.generate_presigned_upload("diagram.png")
            assert result["key"].endswith(".png")

    def test_key_falls_back_to_jpg_for_unknown_extension(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://signed-url.example.com"
            result = media.generate_presigned_upload("malicious.exe")
            assert result["key"].endswith(".jpg")

    def test_key_sanitizes_unsafe_filename_characters(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://signed-url.example.com"
            result = media.generate_presigned_upload("my photo!@#$.jpg")
            stub_segment = result["key"].split("/")[-1]
            assert " " not in stub_segment
            assert "!" not in stub_segment

    def test_two_calls_produce_different_keys(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://signed-url.example.com"
            first = media.generate_presigned_upload("photo.jpg")
            second = media.generate_presigned_upload("photo.jpg")
            assert first["key"] != second["key"]

    def test_browser_endpoint_substitution_applied(self):
        with patch.object(media, "s3_client") as mock_s3, \
             patch.object(media, "_BROWSER_S3_ENDPOINT_URL", "http://localhost:4566"), \
             patch.dict(media.os.environ, {"S3_ENDPOINT_URL": "http://host.docker.internal:4566"}):
            mock_s3.generate_presigned_url.return_value = (
                "http://host.docker.internal:4566/bucket/key?Signature=abc"
            )
            result = media.generate_presigned_upload("photo.jpg")
            assert "host.docker.internal" not in result["upload_url"]
            assert "localhost:4566" in result["upload_url"]

    def test_no_browser_endpoint_leaves_url_untouched(self):
        with patch.object(media, "s3_client") as mock_s3, \
             patch.object(media, "_BROWSER_S3_ENDPOINT_URL", None):
            mock_s3.generate_presigned_url.return_value = "https://real-cloudfront.example.com/key"
            result = media.generate_presigned_upload("photo.jpg")
            assert result["upload_url"] == "https://real-cloudfront.example.com/key"


class TestResolvePendingImages:

    def test_existing_key_passes_through_unchanged(self):
        images = {"content-private-images/2026/06/existing.jpg": {}}
        clean, upload_urls, replacements = media.resolve_pending_images(images)
        assert clean == {"content-private-images/2026/06/existing.jpg": {}}
        assert upload_urls == {}
        assert replacements == {}

    def test_pending_entry_generates_private_key(self):
        with patch.object(media, "generate_presigned_upload") as mock_upload, \
             patch.object(media, "generate_presigned_read") as mock_read:
            mock_upload.return_value = {
                "key": "content-private-images/2026/06/new.jpg",
                "upload_url": "https://signed.example.com",
            }
            mock_read.return_value = "https://presigned-read.example.com/new.jpg"
            images = {"blob:http://localhost:5173/abc": {"filename": "photo.jpg"}}
            clean, upload_urls, replacements = media.resolve_pending_images(images)

            assert "content-private-images/2026/06/new.jpg" in clean
            assert clean["content-private-images/2026/06/new.jpg"] == {}
            entry = upload_urls["blob:http://localhost:5173/abc"]
            assert entry["key"] == "content-private-images/2026/06/new.jpg"
            assert entry["display_url"] == "https://presigned-read.example.com/new.jpg"

    def test_pending_entry_body_replacement_is_marker(self):
        with patch.object(media, "generate_presigned_upload") as mock_upload, \
             patch.object(media, "generate_presigned_read") as mock_read:
            mock_upload.return_value = {
                "key": "content-private-images/2026/06/new.jpg",
                "upload_url": "https://signed.example.com",
            }
            mock_read.return_value = "https://presigned-read.example.com/new.jpg"
            images = {"blob:http://localhost:5173/abc": {"filename": "photo.jpg"}}
            _, _, replacements = media.resolve_pending_images(images)

            assert replacements == {
                "blob:http://localhost:5173/abc": "media-key:content-private-images/2026/06/new.jpg"
            }

    def test_mixed_existing_and_pending(self):
        with patch.object(media, "generate_presigned_upload") as mock_upload, \
             patch.object(media, "generate_presigned_read") as mock_read:
            mock_upload.return_value = {
                "key": "content-private-images/2026/06/new.jpg",
                "upload_url": "https://signed.example.com",
            }
            mock_read.return_value = "https://presigned-read.example.com/new.jpg"
            images = {
                "content-private-images/2026/05/old.jpg": {},
                "blob:http://localhost:5173/abc": {"filename": "photo.jpg"},
            }
            clean, upload_urls, replacements = media.resolve_pending_images(images)

            assert "content-private-images/2026/05/old.jpg" in clean
            assert "content-private-images/2026/06/new.jpg" in clean
            assert len(upload_urls) == 1
            assert len(replacements) == 1

    def test_empty_dict_returns_empty_everything(self):
        clean, upload_urls, replacements = media.resolve_pending_images({})
        assert clean == {}
        assert upload_urls == {}
        assert replacements == {}

    def test_none_input_returns_empty_everything(self):
        clean, upload_urls, replacements = media.resolve_pending_images(None)
        assert clean == {}
        assert upload_urls == {}
        assert replacements == {}

    def test_entry_without_filename_treated_as_existing(self):
        with patch.object(media, "generate_presigned_upload") as mock_upload:
            images = {"some-key": {"alt": "a description"}}
            clean, upload_urls, replacements = media.resolve_pending_images(images)
            mock_upload.assert_not_called()
            assert clean == {"some-key": {"alt": "a description"}}


class TestApplyBodyReplacements:

    def test_single_replacement(self):
        body = '<img src="blob:http://localhost:5173/abc">'
        replacements = {"blob:http://localhost:5173/abc": "https://cdn.example.com/key.jpg"}
        result = media.apply_body_replacements(body, replacements)
        assert result == '<img src="https://cdn.example.com/key.jpg">'

    def test_multiple_replacements(self):
        body = (
            '<img src="blob:http://localhost:5173/a"><p>text</p>'
            '<img src="blob:http://localhost:5173/b">'
        )
        replacements = {
            "blob:http://localhost:5173/a": "https://cdn.example.com/a.jpg",
            "blob:http://localhost:5173/b": "https://cdn.example.com/b.jpg",
        }
        result = media.apply_body_replacements(body, replacements)
        assert "blob:" not in result
        assert "https://cdn.example.com/a.jpg" in result
        assert "https://cdn.example.com/b.jpg" in result

    def test_no_replacements_returns_body_unchanged(self):
        body = "<p>No images here</p>"
        result = media.apply_body_replacements(body, {})
        assert result == body

    def test_no_match_in_body_leaves_body_unchanged(self):
        body = "<p>No matching blob url</p>"
        replacements = {"blob:http://localhost:5173/abc": "https://cdn.example.com/key.jpg"}
        result = media.apply_body_replacements(body, replacements)
        assert result == body

    def test_repeated_blob_url_all_instances_replaced(self):
        body = (
            '<img src="blob:http://localhost:5173/abc">'
            '<img src="blob:http://localhost:5173/abc">'
        )
        replacements = {"blob:http://localhost:5173/abc": "https://cdn.example.com/key.jpg"}
        result = media.apply_body_replacements(body, replacements)
        assert result.count("https://cdn.example.com/key.jpg") == 2

class TestNormalizeBodyToMarkers:

    def test_private_presigned_url_converted_to_marker(self):
        body = '<img src="https://s3.example.com/content-private-images/2026/06/abc.jpg?Signature=xyz&Expires=123">'
        result = media.normalize_body_to_markers(body)
        assert "media-key:content-private-images/2026/06/abc.jpg" in result
        assert "Signature=" not in result

    def test_public_cdn_url_left_untouched(self):
        body = '<img src="https://cdn.example.com/content-images/2026/06/abc.jpg">'
        result = media.normalize_body_to_markers(body)
        assert result == body

    def test_existing_marker_left_untouched(self):
        body = '<img src="media-key:content-private-images/2026/06/abc.jpg">'
        result = media.normalize_body_to_markers(body)
        assert result == body

    def test_no_private_url_returns_body_unchanged(self):
        body = "<p>No images here</p>"
        result = media.normalize_body_to_markers(body)
        assert result == body

    def test_multiple_private_urls_all_converted(self):
        body = (
            '<img src="https://s3.example.com/content-private-images/2026/06/a.jpg?Signature=x&Expires=1">'
            '<img src="https://s3.example.com/content-private-images/2026/06/b.jpg?Signature=y&Expires=2">'
        )
        result = media.normalize_body_to_markers(body)
        assert "media-key:content-private-images/2026/06/a.jpg" in result
        assert "media-key:content-private-images/2026/06/b.jpg" in result
        assert "Signature=" not in result

    def test_blob_scheme_private_url_converted(self):
        body = '<img src="http://localhost:4566/personal-hub-media/content-private-images/2026/06/abc.jpg?AWSAccessKeyId=fake&Signature=xyz&Expires=123">'
        result = media.normalize_body_to_markers(body)
        assert "media-key:content-private-images/2026/06/abc.jpg" in result


# --- resolve_body_markers_for_display ---

class TestResolveBodyMarkersForDisplay:

    def test_marker_replaced_with_presigned_url(self):
        with patch.object(media, "generate_presigned_read") as mock_read:
            mock_read.return_value = "https://presigned.example.com/abc.jpg"
            body = '<img src="media-key:content-private-images/2026/06/abc.jpg">'
            result = media.resolve_body_markers_for_display(body)
            assert "https://presigned.example.com/abc.jpg" in result
            assert "media-key:" not in result

    def test_no_markers_returns_body_unchanged(self):
        body = '<img src="https://cdn.example.com/content-images/2026/06/abc.jpg">'
        result = media.resolve_body_markers_for_display(body)
        assert result == body

    def test_multiple_markers_all_resolved(self):
        with patch.object(media, "generate_presigned_read") as mock_read:
            mock_read.side_effect = [
                "https://presigned.example.com/a.jpg",
                "https://presigned.example.com/b.jpg",
            ]
            body = (
                '<img src="media-key:content-private-images/2026/06/a.jpg">'
                '<img src="media-key:content-private-images/2026/06/b.jpg">'
            )
            result = media.resolve_body_markers_for_display(body)
            assert "media-key:" not in result
            assert "https://presigned.example.com/a.jpg" in result
            assert "https://presigned.example.com/b.jpg" in result

    def test_empty_body_returns_unchanged(self):
        result = media.resolve_body_markers_for_display("")
        assert result == ""


class TestExtractImageKeysFromBody:

    def test_extracts_private_marker_keys(self):
        body = '<img src="media-key:content-private-images/2026/06/abc.jpg">'
        keys = media.extract_image_keys_from_body(body)
        assert "content-private-images/2026/06/abc.jpg" in keys

    def test_extracts_public_cdn_keys(self):
        body = '<img src="https://cdn.example.com/content-images/2026/06/abc.jpg">'
        keys = media.extract_image_keys_from_body(body)
        assert "content-images/2026/06/abc.jpg" in keys

    def test_extracts_mixed_markers_and_public(self):
        body = (
            '<img src="media-key:content-private-images/2026/06/a.jpg">'
            '<img src="https://cdn.example.com/content-images/2026/06/b.jpg">'
        )
        keys = media.extract_image_keys_from_body(body)
        assert "content-private-images/2026/06/a.jpg" in keys
        assert "content-images/2026/06/b.jpg" in keys

    def test_no_images_returns_empty_set(self):
        body = "<p>No images here</p>"
        keys = media.extract_image_keys_from_body(body)
        assert keys == set()

    def test_empty_body_returns_empty_set(self):
        keys = media.extract_image_keys_from_body("")
        assert keys == set()


class TestPromoteToPublic:

    def test_moves_private_key_to_public(self):
        with patch.object(media, "s3_client") as mock_s3:
            keys = {"content-private-images/2026/06/abc.jpg"}
            moved = media.promote_to_public(keys)
            assert moved == {"content-private-images/2026/06/abc.jpg": "content-images/2026/06/abc.jpg"}
            mock_s3.copy_object.assert_called_once()
            mock_s3.delete_object.assert_called_once()

    def test_already_public_key_skipped(self):
        with patch.object(media, "s3_client") as mock_s3:
            keys = {"content-images/2026/06/abc.jpg"}
            moved = media.promote_to_public(keys)
            assert moved == {}
            mock_s3.copy_object.assert_not_called()

    def test_failed_copy_does_not_raise(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.copy_object.side_effect = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "CopyObject"
            )
            moved = media.promote_to_public({"content-private-images/2026/06/abc.jpg"})
            assert moved == {}

    def test_domain_parameter_respected(self):
        with patch.object(media, "s3_client") as mock_s3:
            keys = {"wiki-private-images/2026/06/abc.jpg"}
            moved = media.promote_to_public(keys, domain="wiki")
            assert moved == {"wiki-private-images/2026/06/abc.jpg": "wiki-images/2026/06/abc.jpg"}


class TestDemoteToPrivate:

    def test_moves_public_key_to_private(self):
        with patch.object(media, "s3_client") as mock_s3:
            keys = {"content-images/2026/06/abc.jpg"}
            moved = media.demote_to_private(keys)
            assert moved == {"content-images/2026/06/abc.jpg": "content-private-images/2026/06/abc.jpg"}
            mock_s3.copy_object.assert_called_once()
            mock_s3.delete_object.assert_called_once()

    def test_already_private_key_skipped(self):
        with patch.object(media, "s3_client") as mock_s3:
            keys = {"content-private-images/2026/06/abc.jpg"}
            moved = media.demote_to_private(keys)
            assert moved == {}
            mock_s3.copy_object.assert_not_called()

    def test_failed_copy_does_not_raise(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.copy_object.side_effect = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "CopyObject"
            )
            moved = media.demote_to_private({"content-images/2026/06/abc.jpg"})
            assert moved == {}


class TestRewriteBodyForMovedImages:

    def test_promoted_key_marker_replaced_with_public_url(self):
        with patch.dict(media.os.environ, {"MEDIA_CDN_DOMAIN": "cdn.example.com"}):
            body = '<img src="media-key:content-private-images/2026/06/abc.jpg">'
            moved = {"content-private-images/2026/06/abc.jpg": "content-images/2026/06/abc.jpg"}
            result = media.rewrite_body_for_moved_images(body, moved)
            assert "media-key:" not in result
            assert "content-images/2026/06/abc.jpg" in result

    def test_demoted_key_public_url_replaced_with_marker(self):
        with patch.object(media, "generate_presigned_read") as mock_read, \
             patch.dict(media.os.environ, {"MEDIA_CDN_DOMAIN": "cdn.example.com"}):
            mock_read.return_value = "https://presigned.example.com/abc.jpg"
            body = f'<img src="{media.CDN_SCHEME}://cdn.example.com/content-images/2026/06/abc.jpg">'
            moved = {"content-images/2026/06/abc.jpg": "content-private-images/2026/06/abc.jpg"}
            result = media.rewrite_body_for_moved_images(body, moved)
            assert "media-key:content-private-images/2026/06/abc.jpg" in result
            assert "content-images/2026/06/abc.jpg" not in result

    def test_no_moved_keys_returns_body_unchanged(self):
        body = "<p>No images</p>"
        result = media.rewrite_body_for_moved_images(body, {})
        assert result == body