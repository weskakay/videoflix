import django_rq
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from video_app.models import Video
from video_app.tasks import process_video
from video_app.utils import clear_video_cache, delete_video_files


def queue_conversion(video_id):
    """Hands the conversion of a video to the RQ worker."""
    queue = django_rq.get_queue('default', autocommit=True)
    queue.enqueue(process_video, video_id)


@receiver(post_save, sender=Video)
def convert_new_video(sender, instance, created, **kwargs):
    """Clears the cached list and converts new videos after the commit.

    Without on_commit the worker could look for a row that is not saved yet.
    """
    transaction.on_commit(clear_video_cache)
    if created:
        transaction.on_commit(lambda: queue_conversion(instance.id))


@receiver(post_delete, sender=Video)
def remove_video_files(sender, instance, **kwargs):
    """Deletes all files of a video once its row is gone for good."""
    transaction.on_commit(clear_video_cache)
    transaction.on_commit(lambda: delete_video_files(instance))
