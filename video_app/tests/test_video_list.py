from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from video_app.models import Video
from video_app.tests.helpers import create_video, use_temp_media


def mark_converted(video):
    """Sets the state the background job leaves behind."""
    Video.objects.filter(pk=video.pk).update(
        is_converted=True, thumbnail=f'thumbnails/{video.pk}.jpg'
    )


class VideoListTests(APITestCase):
    """Covers GET /api/video/."""

    def setUp(self):
        use_temp_media(self)
        cache.clear()
        self.user = User.objects.create_user('max@mail.de', password='x')
        self.client.force_authenticate(self.user)
        self.url = reverse('video-list')
        self.older = create_video(title='Older')
        self.newer = create_video(title='Newer', category='Action')
        mark_converted(self.older)
        mark_converted(self.newer)

    def test_requires_login(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lists_newest_first(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [video['title'] for video in response.data]
        self.assertEqual(titles, ['Newer', 'Older'])

    def test_fields_in_documented_order(self):
        response = self.client.get(self.url)
        self.assertEqual(list(response.data[0]), [
            'id', 'created_at', 'title', 'description',
            'thumbnail_url', 'category',
        ])
        self.assertEqual(response.data[0]['category'], 'Action')

    def test_thumbnail_url_is_absolute(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response.data[0]['thumbnail_url'],
            f'http://testserver/media/thumbnails/{self.newer.pk}.jpg',
        )

    def test_unconverted_video_is_hidden(self):
        create_video(title='Still converting')
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 2)

    def test_empty_list(self):
        Video.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.data, [])

    def test_second_request_comes_from_cache(self):
        self.client.get(self.url)
        with self.assertNumQueries(0):
            response = self.client.get(self.url)
        self.assertEqual(len(response.data), 2)

    def test_video_without_thumbnail(self):
        Video.objects.filter(pk=self.newer.pk).update(thumbnail='')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data[0]['thumbnail_url'])

    def test_saving_a_video_clears_the_cache(self):
        self.client.get(self.url)
        self.older.refresh_from_db()
        self.older.title = 'Renamed'
        with self.captureOnCommitCallbacks(execute=True):
            self.older.save()
        response = self.client.get(self.url)
        self.assertIn('Renamed', [video['title'] for video in response.data])

    def test_cache_is_kept_until_commit(self):
        self.client.get(self.url)
        with self.captureOnCommitCallbacks(execute=False):
            self.older.delete()
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 2)

    def test_deleting_a_video_clears_the_cache(self):
        self.client.get(self.url)
        with self.captureOnCommitCallbacks(execute=True):
            self.older.delete()
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
