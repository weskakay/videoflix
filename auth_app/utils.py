from email.mime.image import MIMEImage
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

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
