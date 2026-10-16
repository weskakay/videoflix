from auth_app.utils import send_html_mail


def send_activation_email(email, activation_link):
    """Sends the mail with the link that activates a new account."""
    send_html_mail(
        'Confirm your email',
        email,
        'auth_app/emails/confirm_email.html',
        'auth_app/emails/confirm_email.txt',
        {'email': email, 'activation_link': activation_link},
    )
