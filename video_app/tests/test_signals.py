from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from video_app.tasks import process_video
from video_app.tests.helpers import create_video, use_temp_media
from video_app.utils import get_hls_dir


class SignalTests(TestCase):
    """Covers starting the conversion and cleaning up files."""

    def setUp(self):
        use_temp_media(self)
        patcher = patch('video_app.signals.django_rq.get_queue')
        self.get_queue = patcher.start()
        self.addCleanup(patcher.stop)

    def test_new_video_queues_conversion_after_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            video = create_video()
        self.get_queue.assert_called_once_with('default', autocommit=True)
        self.get_queue.return_value.enqueue.assert_called_once_with(
            process_video, video.id
        )

    def test_nothing_is_queued_before_commit(self):
        with self.captureOnCommitCallbacks(execute=False):
            create_video()
        self.get_queue.assert_not_called()

    def test_saving_again_queues_nothing(self):
        with self.captureOnCommitCallbacks(execute=True):
            video = create_video()
        with self.captureOnCommitCallbacks(execute=True):
            video.title = 'Renamed'
            video.save()
        self.get_queue.return_value.enqueue.assert_called_once()

    def test_delete_removes_all_files(self):
        video = create_video()
        upload = Path(video.video_file.path)
        hls_file = get_hls_dir(video.id) / '480p' / 'index.m3u8'
        hls_file.parent.mkdir(parents=True)
        hls_file.write_text('#EXTM3U')
        with self.captureOnCommitCallbacks(execute=True):
            video.delete()
        self.assertFalse(upload.exists())
        self.assertFalse(get_hls_dir(video.id).exists())

    def test_delete_without_hls_files_works(self):
        video = create_video()
        upload = Path(video.video_file.path)
        with self.captureOnCommitCallbacks(execute=True):
            video.delete()
        self.assertFalse(upload.exists())

    def test_files_stay_until_commit(self):
        video = create_video()
        upload = Path(video.video_file.path)
        with self.captureOnCommitCallbacks(execute=False):
            video.delete()
        self.assertTrue(upload.exists())
