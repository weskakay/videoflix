import django_rq
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator

from auth_app.tasks import send_activation_email, send_password_reset_email
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


def request_password_reset(email):
    """Queues a reset mail if an active account uses this email.

    Unknown or inactive addresses are skipped without a hint, the caller
    always gets the same answer.
    """
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        return
    token = default_token_generator.make_token(user)
    link = build_frontend_link('confirm_password.html', user, token)
    queue = django_rq.get_queue('default', autocommit=True)
    queue.enqueue(send_password_reset_email, user.email, link)


def reset_password(user, new_password):
    """Stores the new password, the reset link stops working with it."""
    user.set_password(new_password)
    user.save(update_fields=['password'])
