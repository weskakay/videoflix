from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """Videos, HLS conversion and streaming."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'
