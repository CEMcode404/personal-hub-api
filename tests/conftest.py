import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Environment variables needed at *import time* by modules under test
# (e.g. src/utils/media.py reads MEDIA_BUCKET_NAME at module load).
# setdefault is used so this never overrides a real value if one is
# already provided by the shell, CI, or another env-setup mechanism.
os.environ.setdefault("MEDIA_BUCKET_NAME", "test-media-bucket")
os.environ.setdefault("MEDIA_CDN_DOMAIN", "cdn.test.example.com")