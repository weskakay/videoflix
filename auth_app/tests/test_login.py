from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

STRONG_PASSWORD = 'VideoFlix#2026'
GENERAL_ERROR = {'detail': 'Please check your input and try again.'}


class LoginTests(APITestCase):
    """Covers POST /api/login/."""

    def setUp(self):
        self.url = reverse('login')
        self.user = User.objects.create_user(
            'max@mail.de', 'max@mail.de', STRONG_PASSWORD
        )
        self.payload = {'email': 'max@mail.de', 'password': STRONG_PASSWORD}

    def post(self):
        return self.client.post(self.url, self.payload, format='json')

    def assert_general_error(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, GENERAL_ERROR)
        self.assertNotIn('access_token', response.cookies)

    def test_login_returns_200_with_user(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'detail': 'Login successful',
            'user': {'id': self.user.id, 'username': 'max@mail.de'},
        })

    def test_login_sets_httponly_cookies(self):
        response = self.post()
        for name in ('access_token', 'refresh_token'):
            cookie = response.cookies[name]
            self.assertTrue(cookie.value)
            self.assertTrue(cookie['httponly'])
            self.assertEqual(cookie['samesite'], 'Lax')

    def test_cookies_live_as_long_as_tokens(self):
        response = self.post()
        self.assertEqual(response.cookies['access_token']['max-age'], 3600)
        self.assertEqual(response.cookies['refresh_token']['max-age'], 86400)

    @override_settings(JWT_COOKIE_SECURE=True)
    def test_cookies_are_secure_when_configured(self):
        response = self.post()
        self.assertTrue(response.cookies['access_token']['secure'])
        self.assertTrue(response.cookies['refresh_token']['secure'])

    def test_tokens_never_in_body(self):
        response = self.post()
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)

    def test_email_in_other_case(self):
        self.payload['email'] = 'MAX@Mail.de'
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_broken_cookie_does_not_block(self):
        self.client.cookies['access_token'] = 'broken'
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_wrong_password(self):
        self.payload['password'] = 'wrong-password'
        self.assert_general_error()

    def test_unknown_email(self):
        self.payload['email'] = 'nobody@mail.de'
        self.assert_general_error()

    def test_invalid_email_format(self):
        self.payload['email'] = 'not-an-email'
        self.assert_general_error()

    def test_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        self.assert_general_error()

    def test_each_required_field_missing(self):
        for field in ('email', 'password'):
            payload = dict(self.payload)
            del self.payload[field]
            self.assert_general_error()
            self.payload = payload

    def test_username_instead_of_email(self):
        self.payload = {'username': 'max@mail.de', 'password': STRONG_PASSWORD}
        self.assert_general_error()

    def test_login_kills_old_activation_link(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        self.post()
        response = self.client.get(reverse('activate', args=[uid, token]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
