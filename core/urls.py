"""URL configuration for the Videoflix project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('auth_app.api.urls')),
    path('api/', include('video_app.api.urls')),
]

# Only thumbnails are public, videos and HLS files need a login and go
# through the API. Django serves them while DEBUG is on.
urlpatterns += static(
    f'{settings.MEDIA_URL}thumbnails/',
    document_root=settings.MEDIA_ROOT / 'thumbnails',
)
