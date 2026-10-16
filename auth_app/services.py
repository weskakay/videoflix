from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator


def register_user(email, password):
    """Creates an inactive user and returns it with its activation token.

    The email doubles as username, the account stays locked until the
    link from the activation mail is opened.
    """
    user = User.objects.create_user(
        username=email, email=email, password=password, is_active=False
    )
    token = default_token_generator.make_token(user)
    return user, token
