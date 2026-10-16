from rest_framework import serializers

from video_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    """One entry of the video list with an absolute thumbnail URL."""

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id',
            'created_at',
            'title',
            'description',
            'thumbnail_url',
            'category',
        ]

    def get_thumbnail_url(self, video):
        """Builds the full URL, the frontend runs on another origin."""
        if not video.thumbnail:
            return None
        request = self.context['request']
        return request.build_absolute_uri(video.thumbnail.url)
