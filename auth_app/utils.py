from email.mime.image import MIMEImage
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

LOGO_PATH = Path(__file__).resolve().parent / 'static/auth_app/logo.png'


def build_frontend_link(page, user, token):
    """Returns the frontend link with uid and token for an email."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    query = urlencode({'uid': uid, 'token': token})
    return f'{settings.FRONTEND_URL}/pages/auth/{page}?{query}'


def find_user_by_uid(uidb64):
    """Returns the user behind a uid from a mail link, or None."""
    try:
        user_id = int(force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError):
        return None
    return User.objects.filter(pk=user_id).first()


def attach_logo(message):
    """Embeds the logo, so the mail does not load images from outside."""
    with open(LOGO_PATH, 'rb') as logo_file:
        logo = MIMEImage(logo_file.read())
    logo.add_header('Content-ID', '<logo>')
    logo.add_header('Content-Disposition', 'inline', filename='logo.png')
    message.attach(logo)


def send_html_mail(subject, recipient, html_template, text_template,
                   context):
    """Sends a mail with an HTML part, a plain text part and the logo."""
    text_body = render_to_string(text_template, context)
    html_body = render_to_string(html_template, context)
    message = EmailMultiAlternatives(subject, text_body, to=[recipient])
    message.attach_alternative(html_body, 'text/html')
    message.mixed_subtype = 'related'
    attach_logo(message)
    message.send()


def set_token_cookie(response, name, token, lifetime):
    """Stores a JWT in an HttpOnly cookie that expires with the token."""
    response.set_cookie(
        name,
        str(token),
        max_age=int(lifetime.total_seconds()),
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite='Lax',
    )


def set_access_cookie(response, token):
    """Sets the short lived access token cookie."""
    lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
    set_token_cookie(response, 'access_token', token, lifetime)


def set_refresh_cookie(response, token):
    """Sets the refresh token cookie."""
    lifetime = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
    set_token_cookie(response, 'refresh_token', token, lifetime)


def delete_token_cookies(response):
    """Removes both JWT cookies from the browser."""
    response.delete_cookie('access_token', samesite='Lax')
    response.delete_cookie('refresh_token', samesite='Lax')


def blacklist_refresh_token(raw_token):
    """Puts the refresh token on the blacklist so it cannot be used again.

    A broken or already blacklisted token has nothing left to block,
    the logout goes on anyway.
    """
    try:
        RefreshToken(raw_token).blacklist()
    except TokenError:
        pass
