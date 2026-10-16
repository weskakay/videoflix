from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.tasks import send_password_reset_email

SUCCESS = {'detail': 'An email has been sent to reset your password.'}


class PasswordResetTests(APITestCase):
    """Covers POST /api/password_reset/."""

    def setUp(self):
        patcher = patch('auth_app.services.django_rq.get_queue')
        self.get_queue = patcher.start()
        self.addCleanup(patcher.stop)
        self.enqueue = self.get_queue.return_value.enqueue
        self.user = User.objects.create_user(
            'max@mail.de', 'max@mail.de', 'VideoFlix#2026'
        )
        self.url = reverse('password-reset')

    def post(self, email):
        return self.client.post(self.url, {'email': email}, format='json')

    def test_known_email_returns_200_and_queues_mail(self):
        response = self.post('max@mail.de')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, SUCCESS)
        args = self.enqueue.call_args.args
        self.assertEqual(args[:2], (send_password_reset_email, 'max@mail.de'))
        self.assertIn('/pages/auth/confirm_password.html?uid=', args[2])

    def test_email_in_other_case(self):
        self.post('MAX@Mail.de')
        self.enqueue.assert_called_once()

    def test_unknown_email_gives_same_answer_without_mail(self):
        response = self.post('nobody@mail.de')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, SUCCESS)
        self.enqueue.assert_not_called()

    def test_inactive_user_gets_no_mail(self):
        self.user.is_active = False
        self.user.save()
        response = self.post('max@mail.de')
        self.assertEqual(response.data, SUCCESS)
        self.enqueue.assert_not_called()

    def test_invalid_email_format(self):
        response = self.post('not-an-email')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.enqueue.assert_not_called()

    def test_missing_email(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_broken_cookie_does_not_block(self):
        self.client.cookies['access_token'] = 'broken'
        response = self.post('max@mail.de')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
