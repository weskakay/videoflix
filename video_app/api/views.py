from django.http import FileResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from video_app.api.serializers import VideoSerializer
from video_app.models import Video
from video_app.utils import find_hls_file, get_cached_videos


class VideoListView(generics.ListAPIView):
    """GET /api/video/ lists all converted videos, newest first.

    The list is cached in Redis, saving or deleting a video clears it.
    """

    permission_classes = [IsAuthenticated]
    queryset = Video.objects.filter(is_converted=True)
    serializer_class = VideoSerializer

    def list(self, request, *args, **kwargs):
        """Answers from the cache when possible."""
        videos = get_cached_videos(self.get_queryset())
        serializer = self.get_serializer(videos, many=True)
        return Response(serializer.data)


class HlsManifestView(generics.GenericAPIView):
    """GET /api/video/<movie_id>/<resolution>/index.m3u8"""

    permission_classes = [IsAuthenticated]
    queryset = Video.objects.filter(is_converted=True)
    lookup_url_kwarg = 'movie_id'

    def get(self, request, movie_id, resolution):
        """Sends the HLS playlist of one resolution."""
        video = self.get_object()
        path = find_hls_file(video.id, resolution, 'index.m3u8')
        return FileResponse(
            open(path, 'rb'), content_type='application/vnd.apple.mpegurl'
        )


class HlsSegmentView(generics.GenericAPIView):
    """GET /api/video/<movie_id>/<resolution>/<segment>/"""

    permission_classes = [IsAuthenticated]
    queryset = Video.objects.filter(is_converted=True)
    lookup_url_kwarg = 'movie_id'

    def get(self, request, movie_id, resolution, segment):
        """Sends one video segment of a resolution."""
        video = self.get_object()
        path = find_hls_file(video.id, resolution, segment)
        return FileResponse(open(path, 'rb'), content_type='video/MP2T')
