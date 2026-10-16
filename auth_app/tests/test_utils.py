from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from auth_app.utils import build_frontend_link, find_user_by_uid


@override_settings(FRONTEND_URL='http://frontend.test')
class FrontendLinkTests(TestCase):
    """Covers build_frontend_link and find_user_by_uid."""

    def setUp(self):
        self.user = User.objects.create_user(
            'max@mail.de', 'max@mail.de', 'x'
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))

    def test_link_contains_page_uid_and_token(self):
        link = build_frontend_link('activate.html', self.user, 'abc-123')
        self.assertEqual(
            link,
            'http://frontend.test/pages/auth/activate.html'
            f'?uid={self.uid}&token=abc-123',
        )

    def test_uid_from_link_finds_the_user(self):
        self.assertEqual(find_user_by_uid(self.uid), self.user)

    def test_broken_uid_finds_nobody(self):
        self.assertIsNone(find_user_by_uid('%%%'))
