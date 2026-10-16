import shutil
from pathlib import Path

from django.conf import settings

# Name in the URL and the size FFmpeg scales the video to.
RESOLUTIONS = {
    '480p': 'hd480',
    '720p': 'hd720',
    '1080p': 'hd1080',
}


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
