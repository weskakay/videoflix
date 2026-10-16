from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

GENERAL_ERROR = {'detail': 'Please check your input and try again.'}


def encode(value):
    """Encodes a value the way the mail links do."""
    return urlsafe_base64_encode(force_bytes(value))


class ActivationTests(APITestCase):
    """Covers GET /api/activate/<uidb64>/<token>/."""

    def setUp(self):
        self.user = User.objects.create_user(
            'max@mail.de', 'max@mail.de', 'VideoFlix#2026', is_active=False
        )
        self.uid = encode(self.user.pk)
        self.token = default_token_generator.make_token(self.user)

    def activate(self, uid, token):
        url = reverse('activate', args=[uid, token])
        return self.client.get(url)

    def assert_invalid(self, uid, token):
        response = self.activate(uid, token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, GENERAL_ERROR)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_valid_link_activates_user(self):
        response = self.activate(self.uid, self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, {'message': 'Account successfully activated.'}
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_second_click_still_succeeds(self):
        self.activate(self.uid, self.token)
        response = self.activate(self.uid, self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_link_is_dead_after_first_login(self):
        self.activate(self.uid, self.token)
        self.user.last_login = timezone.now()
        self.user.save()
        response = self.activate(self.uid, self.token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_token(self):
        self.assert_invalid(self.uid, 'wrong-token')

    def test_token_of_another_user(self):
        other = User.objects.create_user('eva@mail.de', 'eva@mail.de', 'x')
        other_token = default_token_generator.make_token(other)
        self.assert_invalid(self.uid, other_token)

    def test_unknown_user(self):
        self.assert_invalid(encode(self.user.pk + 100), self.token)

    def test_uid_is_not_base64(self):
        self.assert_invalid('%%%', self.token)

    def test_uid_is_not_a_number(self):
        self.assert_invalid(encode('abc'), self.token)

    def test_uid_too_large_for_database(self):
        self.assert_invalid(encode('9' * 20), self.token)

    def test_negative_uid(self):
        self.assert_invalid(encode('-99999999999'), self.token)

    def test_broken_cookie_does_not_block(self):
        self.client.cookies['access_token'] = 'broken'
        response = self.activate(self.uid, self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_is_not_allowed(self):
        url = reverse('activate', args=[self.uid, self.token])
        response = self.client.post(url)
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )
