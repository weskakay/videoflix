import subprocess
from pathlib import Path

from django.conf import settings

from video_app.models import Video
from video_app.utils import (
    RESOLUTIONS,
    build_hls_command,
    build_thumbnail_command,
    get_hls_dir,
)


def convert_to_hls(source, video_id, resolution):
    """Creates index.m3u8 and the segments of one resolution."""
    target_dir = get_hls_dir(video_id) / resolution
    target_dir.mkdir(parents=True, exist_ok=True)
    command = build_hls_command(source, target_dir, RESOLUTIONS[resolution])
    subprocess.run(command, check=True)


def create_thumbnail(source, video_id):
    """Saves a still image of the video and returns its media path."""
    name = f'thumbnails/{video_id}.jpg'
    target = Path(settings.MEDIA_ROOT) / name
    target.parent.mkdir(parents=True, exist_ok=True)
    command = build_thumbnail_command(source, target)
    subprocess.run(command, check=True)
    return name


def process_video(video_id):
    """Background job: converts all resolutions, then marks the video.

    An uploaded thumbnail is kept, otherwise one is taken from the video.
    The update() call skips the post_save signal on purpose. A video
    deleted before the job starts has nothing left to convert.
    """
    video = Video.objects.filter(pk=video_id).first()
    if video is None:
        return
    source = video.video_file.path
    for resolution in RESOLUTIONS:
        convert_to_hls(source, video_id, resolution)
    thumbnail = video.thumbnail.name or create_thumbnail(source, video_id)
    Video.objects.filter(pk=video_id).update(
        thumbnail=thumbnail, is_converted=True
    )
