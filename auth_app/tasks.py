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


def send_password_reset_email(email, reset_link):
    """Sends the mail with the link to choose a new password."""
    send_html_mail(
        'Reset your Password',
        email,
        'auth_app/emails/password_reset.html',
        'auth_app/emails/password_reset.txt',
        {'reset_link': reset_link},
    )
