from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class TokenRefreshTests(APITestCase):
    """Covers POST /api/token/refresh/."""

    def setUp(self):
        self.user = User.objects.create_user('max@mail.de', password='x')
        self.refresh = RefreshToken.for_user(self.user)
        self.client.cookies['refresh_token'] = str(self.refresh)
        self.url = reverse('token-refresh')

    def test_refresh_returns_200_with_new_access(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), ['detail', 'access'])
        self.assertEqual(response.data['detail'], 'Token refreshed')
        access = AccessToken(response.data['access'])
        self.assertEqual(str(access['user_id']), str(self.user.id))

    def test_refresh_sets_new_access_cookie(self):
        response = self.client.post(self.url)
        cookie = response.cookies['access_token']
        self.assertEqual(cookie.value, response.data['access'])
        self.assertTrue(cookie['httponly'])
        self.assertNotIn('refresh_token', response.cookies)

    def test_missing_cookie_returns_400(self):
        self.client.cookies.clear()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {'detail': 'Refresh token is missing.'}
        )

    def test_broken_cookie_returns_401(self):
        self.client.cookies['refresh_token'] = 'garbage'
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blacklisted_token_returns_401(self):
        self.refresh.blacklist()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_token_as_refresh_returns_401(self):
        self.client.cookies['refresh_token'] = str(self.refresh.access_token)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
