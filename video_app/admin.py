from django.contrib import admin

from video_app.models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Upload and manage videos, the conversion state is read only."""

    list_display = ['title', 'category', 'is_converted', 'created_at']
    list_filter = ['category', 'is_converted']
    search_fields = ['title', 'description']
    readonly_fields = ['is_converted', 'created_at']
