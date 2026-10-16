from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """Videos, HLS conversion and streaming."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'

    def ready(self):
        """Connects the signals that convert and clean up videos."""
        from video_app import signals  # noqa: F401
