from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """Registration, activation, login and password reset."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_app'
