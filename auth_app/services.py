import django_rq
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator

from auth_app.tasks import send_activation_email
from auth_app.utils import build_frontend_link


@transaction.atomic
def register_user(email, password):
    """Creates an inactive user and queues the activation mail.

    The email doubles as username, the account stays locked until the
    link from the mail is opened. If the mail cannot be queued, the user
    is rolled back, so the address stays free. Returns user and token.
    """
    user = User.objects.create_user(
        username=email, email=email, password=password, is_active=False
    )
    token = default_token_generator.make_token(user)
    link = build_frontend_link('activate.html', user, token)
    queue = django_rq.get_queue('default', autocommit=True)
    queue.enqueue(send_activation_email, user.email, link)
    return user, token


def activate_user(user):
    """Unlocks the account, from now on the user can log in."""
    user.is_active = True
    user.save(update_fields=['is_active'])
