from django.core import mail
from django.test import TestCase

from auth_app.tasks import send_activation_email

LINK = 'http://127.0.0.1:5500/pages/auth/activate.html?uid=MQ&token=abc'


class ActivationEmailTests(TestCase):
    """Covers the send_activation_email job."""

    def setUp(self):
        send_activation_email('max@mail.de', LINK)
        self.assertEqual(len(mail.outbox), 1)
        self.message = mail.outbox[0]

    def test_subject_and_recipient(self):
        self.assertEqual(self.message.subject, 'Confirm your email')
        self.assertEqual(self.message.to, ['max@mail.de'])

    def test_plain_text_contains_raw_link(self):
        self.assertIn(LINK, self.message.body)
        self.assertIn('Dear max@mail.de,', self.message.body)

    def test_html_part_contains_button_link(self):
        html, mimetype = self.message.alternatives[0]
        self.assertEqual(mimetype, 'text/html')
        self.assertIn('Activate account', html)
        self.assertIn(LINK.replace('&', '&amp;'), html)
        self.assertIn('src="cid:logo"', html)

    def test_logo_is_embedded(self):
        logo = self.message.attachments[0]
        self.assertEqual(logo['Content-ID'], '<logo>')
        self.assertEqual(logo.get_content_type(), 'image/png')
