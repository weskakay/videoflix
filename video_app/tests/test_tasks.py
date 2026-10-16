import subprocess
from pathlib import Path
from unittest.mock import call, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from video_app.models import Video
from video_app.tasks import convert_to_hls, create_thumbnail, process_video
from video_app.tests.helpers import create_video, use_temp_media
from video_app.utils import build_hls_command, build_thumbnail_command


@patch('video_app.tasks.subprocess.run')
class ConversionTaskTests(TestCase):
    """Covers the FFmpeg jobs, FFmpeg itself is mocked."""

    def setUp(self):
        self.media_root = Path(use_temp_media(self))
        self.video = create_video()

    def test_convert_to_hls_runs_ffmpeg_for_one_resolution(self, run):
        convert_to_hls('/in.mp4', self.video.id, '720p')
        target = self.media_root / 'hls' / str(self.video.id) / '720p'
        self.assertTrue(target.is_dir())
        run.assert_called_once_with(
            build_hls_command('/in.mp4', target, 'hd720'), check=True
        )

    def test_hls_command_uses_list_and_segment_names(self, run):
        command = build_hls_command('/in.mp4', Path('/out'), 'hd1080')
        self.assertEqual(command[0], 'ffmpeg')
        self.assertIn('hd1080', command)
        self.assertIn('/out/%03d.ts', command)
        self.assertEqual(command[-1], '/out/index.m3u8')

    def test_thumbnail_command_takes_one_frame(self, run):
        command = build_thumbnail_command('/in.mp4', Path('/out/1.jpg'))
        self.assertEqual(command[0], 'ffmpeg')
        self.assertIn('thumbnail,scale=640:-2', command)
        self.assertEqual(command[-1], '/out/1.jpg')

    def test_create_thumbnail_returns_media_path(self, run):
        name = create_thumbnail('/in.mp4', self.video.id)
        self.assertEqual(name, f'thumbnails/{self.video.id}.jpg')
        self.assertTrue((self.media_root / 'thumbnails').is_dir())
        run.assert_called_once()

    def test_process_video_converts_all_resolutions(self, run):
        with patch('video_app.tasks.convert_to_hls') as convert:
            process_video(self.video.id)
        source = self.video.video_file.path
        convert.assert_has_calls([
            call(source, self.video.id, '480p'),
            call(source, self.video.id, '720p'),
            call(source, self.video.id, '1080p'),
        ])

    def test_process_video_marks_video_and_sets_thumbnail(self, run):
        process_video(self.video.id)
        self.video.refresh_from_db()
        self.assertTrue(self.video.is_converted)
        self.assertEqual(
            self.video.thumbnail.name, f'thumbnails/{self.video.id}.jpg'
        )

    def test_uploaded_thumbnail_is_kept(self, run):
        image = SimpleUploadedFile('own.jpg', b'image', 'image/jpeg')
        self.video.thumbnail = image
        self.video.save()
        process_video(self.video.id)
        self.video.refresh_from_db()
        self.assertEqual(self.video.thumbnail.name, 'thumbnails/own.jpg')
        self.assertEqual(run.call_count, 3)

    def test_failed_ffmpeg_leaves_video_unconverted(self, run):
        run.side_effect = subprocess.CalledProcessError(1, 'ffmpeg')
        with self.assertRaises(subprocess.CalledProcessError):
            process_video(self.video.id)
        self.assertFalse(Video.objects.get(pk=self.video.id).is_converted)

    def test_deleted_video_is_skipped(self, run):
        video_id = self.video.id
        self.video.delete()
        process_video(video_id)
        run.assert_not_called()
