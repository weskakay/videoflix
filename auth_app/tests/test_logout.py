from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

STRONG_PASSWORD = 'VideoFlix#2026'


class LogoutTests(APITestCase):
    """Covers POST /api/logout/."""

    def setUp(self):
        User.objects.create_user('max@mail.de', 'max@mail.de', STRONG_PASSWORD)
        self.client.post(
            reverse('login'),
            {'email': 'max@mail.de', 'password': STRONG_PASSWORD},
            format='json',
        )
        self.url = reverse('logout')

    def test_logout_returns_200_with_detail(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'detail': 'Logout successful! All tokens will be deleted. '
                      'Refresh token is now invalid.'
        })

    def test_logout_deletes_both_cookies(self):
        response = self.client.post(self.url)
        for name in ('access_token', 'refresh_token'):
            self.assertEqual(response.cookies[name].value, '')
            self.assertEqual(response.cookies[name]['max-age'], 0)

    def test_old_refresh_token_is_blacklisted(self):
        refresh = self.client.cookies['refresh_token'].value
        self.client.post(self.url)
        self.assertEqual(BlacklistedToken.objects.count(), 1)
        self.client.cookies['refresh_token'] = refresh
        response = self.client.post(reverse('token-refresh'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_refresh_cookie_returns_400(self):
        self.client.cookies.clear()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {'detail': 'Refresh token is missing.'}
        )

    def test_broken_access_cookie_does_not_block(self):
        self.client.cookies['access_token'] = 'broken'
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_broken_refresh_cookie_still_logs_out(self):
        self.client.cookies['refresh_token'] = 'garbage'
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['refresh_token'].value, '')

    def test_second_logout_with_same_token_still_works(self):
        refresh = self.client.cookies['refresh_token'].value
        self.client.post(self.url)
        self.client.cookies['refresh_token'] = refresh
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
