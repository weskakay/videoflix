import shutil
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.http import Http404

# Name in the URL and the size FFmpeg scales the video to.
RESOLUTIONS = {
    '480p': 'hd480',
    '720p': 'hd720',
    '1080p': 'hd1080',
}
VIDEO_LIST_CACHE_KEY = 'video_list'
VIDEO_LIST_CACHE_SECONDS = 60 * 15


def get_hls_dir(video_id):
    """Returns the folder that holds all HLS files of one video."""
    return Path(settings.MEDIA_ROOT) / 'hls' / str(video_id)


def build_hls_command(source, target_dir, size):
    """Returns the FFmpeg arguments for one HLS resolution."""
    return [
        'ffmpeg', '-y', '-loglevel', 'error', '-i', str(source),
        '-s', size,
        '-c:v', 'libx264', '-crf', '23',
        '-c:a', 'aac', '-strict', '-2',
        '-start_number', '0',
        '-hls_time', '10',
        '-hls_list_size', '0',
        '-hls_segment_filename', str(target_dir / '%03d.ts'),
        '-f', 'hls', str(target_dir / 'index.m3u8'),
    ]


def build_thumbnail_command(source, target):
    """Returns the FFmpeg arguments for a typical frame of the video.

    The thumbnail filter picks it from the first frames, so it also works
    for very short clips and rarely shows a black start frame.
    """
    return [
        'ffmpeg', '-y', '-loglevel', 'error', '-i', str(source),
        '-vf', 'thumbnail,scale=640:-2', '-frames:v', '1',
        str(target),
    ]


def delete_file(field_file):
    """Deletes the file behind a FileField, if there is one."""
    if field_file:
        field_file.delete(save=False)


def delete_video_files(video):
    """Removes the upload, the thumbnail and every HLS file of a video."""
    delete_file(video.video_file)
    delete_file(video.thumbnail)
    shutil.rmtree(get_hls_dir(video.id), ignore_errors=True)


def find_hls_file(video_id, resolution, file_name):
    """Returns the path of a manifest or segment, or raises a 404.

    Only known resolutions are accepted, the URL patterns already limit
    the file name, so nothing outside the video folder can be reached.
    """
    if resolution not in RESOLUTIONS:
        raise Http404
    path = get_hls_dir(video_id) / resolution / file_name
    if not path.is_file():
        raise Http404
    return path


def get_cached_videos(queryset):
    """Returns the video list from Redis, loads it on the first call."""
    videos = cache.get(VIDEO_LIST_CACHE_KEY)
    if videos is None:
        videos = list(queryset)
        cache.set(VIDEO_LIST_CACHE_KEY, videos, VIDEO_LIST_CACHE_SECONDS)
    return videos


def clear_video_cache():
    """Drops the cached list, the next request loads it fresh."""
    cache.delete(VIDEO_LIST_CACHE_KEY)
