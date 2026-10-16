import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from video_app.models import Video

# Tests keep their own cache, the Redis of the dev setup stays untouched.
TEST_CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
}


def use_temp_media(test_case):
    """Points MEDIA_ROOT to a fresh folder and uses a local cache."""
    media_root = tempfile.mkdtemp()
    settings_override = override_settings(
        MEDIA_ROOT=media_root, CACHES=TEST_CACHES
    )
    settings_override.enable()
    test_case.addCleanup(settings_override.disable)
    test_case.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
    return media_root


def create_video(title='Ocean', category=Video.Category.DOCUMENTARY):
    """Saves a video with a tiny fake upload."""
    upload = SimpleUploadedFile('clip.mp4', b'fake video', 'video/mp4')
    return Video.objects.create(
        title=title,
        description='A test clip.',
        category=category,
        video_file=upload,
    )
