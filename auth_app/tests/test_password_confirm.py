from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

OLD_PASSWORD = 'VideoFlix#2026'
NEW_PASSWORD = 'NewVideoFlix#2026'
GENERAL_ERROR = {'detail': 'Please check your input and try again.'}


class PasswordConfirmTests(APITestCase):
    """Covers POST /api/password_confirm/<uidb64>/<token>/."""

    def setUp(self):
        self.user = User.objects.create_user(
            'max@mail.de', 'max@mail.de', OLD_PASSWORD
        )
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        self.url = reverse('password-confirm', args=[uid, token])
        self.payload = {
            'new_password': NEW_PASSWORD,
            'confirm_password': NEW_PASSWORD,
        }

    def post(self):
        return self.client.post(self.url, self.payload, format='json')

    def assert_password_unchanged(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, GENERAL_ERROR)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_sets_new_password(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {'detail': 'Your Password has been successfully reset.'},
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertFalse(self.user.check_password(OLD_PASSWORD))

    def test_login_works_with_new_password_only(self):
        self.post()
        login = reverse('login')
        old = {'email': 'max@mail.de', 'password': OLD_PASSWORD}
        new = {'email': 'max@mail.de', 'password': NEW_PASSWORD}
        self.assertEqual(
            self.client.post(login, old).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.post(login, new).status_code, status.HTTP_200_OK
        )

    def test_link_works_only_once(self):
        self.post()
        self.payload['new_password'] = 'Another#Pass2026'
        self.payload['confirm_password'] = 'Another#Pass2026'
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_passwords_do_not_match(self):
        self.payload['confirm_password'] = 'Different#2026'
        self.assert_password_unchanged()

    def test_weak_password(self):
        self.payload['new_password'] = '12345678'
        self.payload['confirm_password'] = '12345678'
        self.assert_password_unchanged()

    def test_password_too_similar_to_email(self):
        self.payload['new_password'] = 'max@mail.de1'
        self.payload['confirm_password'] = 'max@mail.de1'
        self.assert_password_unchanged()

    def test_inactive_user_cannot_reset(self):
        self.user.is_active = False
        self.user.save()
        self.assert_password_unchanged()

    def test_link_older_than_24_hours(self):
        two_days_ago = datetime.now() - timedelta(days=2)
        with patch.object(
            PasswordResetTokenGenerator, '_now', return_value=two_days_ago
        ):
            token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.url = reverse('password-confirm', args=[uid, token])
        self.assert_password_unchanged()

    def test_wrong_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.url = reverse('password-confirm', args=[uid, 'wrong-token'])
        self.assert_password_unchanged()

    def test_unknown_user(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk + 100))
        self.url = reverse('password-confirm', args=[uid, 'abc-123'])
        self.assert_password_unchanged()

    def test_missing_fields(self):
        self.payload = {}
        self.assert_password_unchanged()

    def test_body_is_not_an_object(self):
        self.payload = ['x']
        self.assert_password_unchanged()

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )
