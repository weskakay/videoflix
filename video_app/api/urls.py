from django.urls import path, re_path

from video_app.api.views import HlsManifestView, HlsSegmentView, VideoListView

urlpatterns = [
    path('video/', VideoListView.as_view(), name='video-list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8',
         HlsManifestView.as_view(), name='video-manifest'),
    # hls.js requests segments without the trailing slash
    re_path(r'^video/(?P<movie_id>\d+)/(?P<resolution>\w+)/'
            r'(?P<segment>\d{3}\.ts)/?$',
            HlsSegmentView.as_view(), name='video-segment'),
]
