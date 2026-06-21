from unittest.mock import patch
from botocore.exceptions import ClientError
from src.utils import media

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


class TestGeneratePresignedUpload:

    def test_returns_key_and_upload_url(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://signed-url.example.com"
            result = media.generate_presigned_upload("photo.jpg")
            assert "key" in result
            assert "upload_url" in result
            assert result["upload_url"] == "https://signed-url.example.com"

    def test_key_has_content_images_prefix(self):
        with patch.object(media, "s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://signed-url.example.com"
            result = media.generate_presigned_upload("photo.jpg")
            assert result["key"].startswith("content-images/")

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
        images = {"content-images/2026/06/existing.jpg": {}}
        clean, upload_urls, replacements = media.resolve_pending_images(images)
        assert clean == {"content-images/2026/06/existing.jpg": {}}
        assert upload_urls == {}
        assert replacements == {}

    def test_pending_entry_generates_real_key(self):
        with patch.object(media, "generate_presigned_upload") as mock_presign:
            mock_presign.return_value = {
                "key": "content-images/2026/06/new.jpg",
                "upload_url": "https://signed.example.com",
            }
            images = {"blob:http://localhost:5173/abc": {"filename": "photo.jpg"}}
            clean, upload_urls, replacements = media.resolve_pending_images(images)

            assert "content-images/2026/06/new.jpg" in clean
            assert clean["content-images/2026/06/new.jpg"] == {}
            assert "blob:http://localhost:5173/abc" in upload_urls
            assert upload_urls["blob:http://localhost:5173/abc"]["key"] == "content-images/2026/06/new.jpg"

    def test_pending_entry_produces_body_replacement(self):
        with patch.object(media, "generate_presigned_upload") as mock_presign, \
             patch.dict(media.os.environ, {"MEDIA_CDN_DOMAIN": "cdn.example.com"}):
            mock_presign.return_value = {
                "key": "content-images/2026/06/new.jpg",
                "upload_url": "https://signed.example.com",
            }
            images = {"blob:http://localhost:5173/abc": {"filename": "photo.jpg"}}
            _, _, replacements = media.resolve_pending_images(images)

            assert replacements == {
                "blob:http://localhost:5173/abc": f"{media.CDN_SCHEME}://cdn.example.com/content-images/2026/06/new.jpg"
            }

    def test_mixed_existing_and_pending(self):
        with patch.object(media, "generate_presigned_upload") as mock_presign:
            mock_presign.return_value = {
                "key": "content-images/2026/06/new.jpg",
                "upload_url": "https://signed.example.com",
            }
            images = {
                "content-images/2026/05/old.jpg": {},
                "blob:http://localhost:5173/abc": {"filename": "photo.jpg"},
            }
            clean, upload_urls, replacements = media.resolve_pending_images(images)

            assert "content-images/2026/05/old.jpg" in clean
            assert "content-images/2026/06/new.jpg" in clean
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
        with patch.object(media, "generate_presigned_upload") as mock_presign:
            images = {"some-key": {"alt": "a description"}}
            clean, upload_urls, replacements = media.resolve_pending_images(images)
            mock_presign.assert_not_called()
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