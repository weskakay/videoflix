from django.core.validators import FileExtensionValidator
from django.db import models

VIDEO_EXTENSIONS = ['mp4', 'mov', 'mkv', 'webm', 'avi']


class Video(models.Model):
    """A video uploaded in the admin and streamed as HLS.

    After the upload a background job converts it, until then
    is_converted stays False and the video is not listed.
    """

    class Category(models.TextChoices):
        ACTION = 'Action'
        COMEDY = 'Comedy'
        DOCUMENTARY = 'Documentary'
        DRAMA = 'Drama'
        ROMANCE = 'Romance'

    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices)
    video_file = models.FileField(
        upload_to='videos/',
        validators=[FileExtensionValidator(VIDEO_EXTENSIONS)],
    )
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True)
    is_converted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Video'
        verbose_name_plural = 'Videos'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
