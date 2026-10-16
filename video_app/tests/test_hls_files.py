from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from video_app.models import Video
from video_app.tests.helpers import create_video, use_temp_media
from video_app.utils import get_hls_dir


class HlsFileTests(APITestCase):
    """Covers the manifest and segment routes of a converted video."""

    def setUp(self):
        use_temp_media(self)
        user = User.objects.create_user('max@mail.de', password='x')
        self.client.force_authenticate(user)
        self.video = create_video()
        Video.objects.filter(pk=self.video.pk).update(is_converted=True)
        folder = get_hls_dir(self.video.pk) / '720p'
        folder.mkdir(parents=True)
        (folder / 'index.m3u8').write_text('#EXTM3U\n000.ts\n')
        (folder / '000.ts').write_bytes(b'segment')
        self.base = f'/api/video/{self.video.pk}'

    def manifest_url(self, video_id, resolution):
        return reverse('video-manifest', args=[video_id, resolution])

    def test_manifest_is_sent_as_playlist(self):
        response = self.client.get(self.manifest_url(self.video.pk, '720p'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response['Content-Type'], 'application/vnd.apple.mpegurl'
        )
        self.assertIn(b'000.ts', b''.join(response.streaming_content))

    def test_segment_with_and_without_slash(self):
        for url in (f'{self.base}/720p/000.ts', f'{self.base}/720p/000.ts/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response['Content-Type'], 'video/MP2T')
            self.assertEqual(b''.join(response.streaming_content), b'segment')

    def test_documented_segment_route_name(self):
        url = reverse('video-segment', args=[self.video.pk, '720p', '000.ts'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_requires_login(self):
        self.client.force_authenticate(None)
        for url in (self.manifest_url(self.video.pk, '720p'),
                    f'{self.base}/720p/000.ts'):
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED
            )

    def test_unknown_video(self):
        response = self.client.get(self.manifest_url(9999, '720p'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_video_not_converted_yet(self):
        Video.objects.filter(pk=self.video.pk).update(is_converted=False)
        response = self.client.get(self.manifest_url(self.video.pk, '720p'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_resolution(self):
        for url in (self.manifest_url(self.video.pk, '1081p'),
                    self.manifest_url(self.video.pk, '720P'),
                    f'{self.base}/1081p/000.ts'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_huge_video_id(self):
        url = f'/api/video/{"9" * 25}/720p/000.ts'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_files(self):
        for url in (self.manifest_url(self.video.pk, '480p'),
                    f'{self.base}/720p/001.ts'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_paths_outside_the_video_folder(self):
        for name in ('abc.ts', '0000.ts', '..%2f..%2fsettings.py',
                     '..%2f480p%2f000.ts'):
            response = self.client.get(f'{self.base}/720p/{name}')
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
