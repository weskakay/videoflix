from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from video_app.models import Video
from video_app.tests.helpers import create_video, use_temp_media


class VideoModelTests(TestCase):
    """Covers the Video model and its admin."""

    def setUp(self):
        use_temp_media(self)
        self.video = create_video()

    def test_str_is_title(self):
        self.assertEqual(str(self.video), 'Ocean')

    def test_new_video_is_not_converted(self):
        self.assertFalse(self.video.is_converted)

    def test_newest_video_comes_first(self):
        newer = create_video(title='Newer')
        self.assertEqual(list(Video.objects.all()), [newer, self.video])

    def test_unknown_category_is_rejected(self):
        self.video.category = 'Horror'
        with self.assertRaises(ValidationError):
            self.video.full_clean()

    def test_wrong_file_type_is_rejected(self):
        self.video.video_file = SimpleUploadedFile('notes.txt', b'text')
        with self.assertRaises(ValidationError):
            self.video.full_clean()

    def test_admin_is_registered(self):
        self.assertTrue(admin.site.is_registered(Video))

    def test_admin_pages_open_for_superuser(self):
        User.objects.create_superuser('admin', 'admin@mail.de', 'x')
        self.client.login(username='admin', password='x')
        for name in ('admin:video_app_video_changelist',
                     'admin:video_app_video_add'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
