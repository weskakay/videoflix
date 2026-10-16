from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

STRONG_PASSWORD = 'VideoFlix#2026'
GENERAL_ERROR = {'detail': 'Please check your input and try again.'}


class RegistrationTests(APITestCase):
    """Covers POST /api/register/."""

    def setUp(self):
        self.url = reverse('register')
        self.payload = {
            'email': 'max@mail.de',
            'password': STRONG_PASSWORD,
            'confirmed_password': STRONG_PASSWORD,
            'privacy_policy': 'on',
        }

    def post(self):
        return self.client.post(self.url, self.payload, format='json')

    def assert_general_error(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, GENERAL_ERROR)

    def test_creates_inactive_user(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='max@mail.de')
        self.assertFalse(user.is_active)
        self.assertEqual(user.username, 'max@mail.de')
        self.assertTrue(user.check_password(STRONG_PASSWORD))

    def test_response_contains_user_and_activation_token(self):
        response = self.post()
        user = User.objects.get(email='max@mail.de')
        self.assertEqual(list(response.data), ['user', 'token'])
        self.assertEqual(
            response.data['user'], {'id': user.id, 'email': 'max@mail.de'}
        )
        self.assertTrue(
            default_token_generator.check_token(user, response.data['token'])
        )

    def test_email_is_lowercased(self):
        self.payload['email'] = 'Max@Mail.DE'
        response = self.post()
        self.assertEqual(response.data['user']['email'], 'max@mail.de')

    def test_works_without_privacy_policy_field(self):
        del self.payload['privacy_policy']
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_broken_cookie_does_not_block(self):
        self.client.cookies['access_token'] = 'broken'
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_password_never_in_response(self):
        response = self.post()
        self.assertNotIn(STRONG_PASSWORD, response.content.decode())

    def test_existing_email_in_other_case(self):
        User.objects.create_user('max@mail.de', 'max@mail.de', 'x')
        self.payload['email'] = 'MAX@mail.de'
        self.assert_general_error()

    def test_existing_inactive_email(self):
        self.post()
        self.assert_general_error()
        self.assertEqual(User.objects.filter(email='max@mail.de').count(), 1)

    def test_passwords_do_not_match(self):
        self.payload['confirmed_password'] = 'VideoFlix#2027'
        self.assert_general_error()
        self.assertFalse(User.objects.filter(email='max@mail.de').exists())

    def test_weak_passwords(self):
        for password in ('12345678', 'password', 'short1!'):
            self.payload['password'] = password
            self.payload['confirmed_password'] = password
            self.assert_general_error()

    def test_password_too_similar_to_email(self):
        self.payload['password'] = 'max@mail.de1'
        self.payload['confirmed_password'] = 'max@mail.de1'
        self.assert_general_error()

    def test_invalid_email(self):
        self.payload['email'] = 'not-an-email'
        self.assert_general_error()

    def test_email_longer_than_username_field(self):
        self.payload['email'] = 'a' * 143 + '@mail.de'
        self.assert_general_error()

    def test_each_required_field_missing(self):
        for field in ('email', 'password', 'confirmed_password'):
            payload = dict(self.payload)
            del self.payload[field]
            self.assert_general_error()
            self.payload = payload

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )
