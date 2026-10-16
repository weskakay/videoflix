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
    """Starts the conversion once a new video is saved.

    The job is queued after the commit, otherwise the worker could look
    for a video that is not in the database yet. Every save drops the
    cached list after the commit, so changes in the admin show up at once.
    """
    transaction.on_commit(clear_video_cache)
    if created:
        transaction.on_commit(lambda: queue_conversion(instance.id))


@receiver(post_delete, sender=Video)
def remove_video_files(sender, instance, **kwargs):
    """Deletes all files of a video once its row is gone for good."""
    transaction.on_commit(clear_video_cache)
    transaction.on_commit(lambda: delete_video_files(instance))
