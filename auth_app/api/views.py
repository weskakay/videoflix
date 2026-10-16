from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from auth_app.api.exceptions import InvalidInput, MissingRefreshToken
from auth_app.api.serializers import (
    ActivationSerializer,
    EmailTokenObtainSerializer,
    PasswordConfirmSerializer,
    PasswordResetSerializer,
    RegistrationSerializer,
)
from auth_app.services import (
    activate_user,
    register_user,
    request_password_reset,
    reset_password,
)
from auth_app.utils import (
    blacklist_refresh_token,
    delete_token_cookies,
    set_access_cookie,
    set_refresh_cookie,
)


class RegistrationView(generics.CreateAPIView):
    """POST /api/register/ creates an account that still needs activation.

    No authentication runs here, so an expired cookie sent by the
    frontend cannot block the request.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs):
        """Registers the user and answers with id, email and token."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            raise InvalidInput()
        user, token = register_user(
            serializer.validated_data['email'],
            serializer.validated_data['password'],
        )
        body = {'user': {'id': user.id, 'email': user.email}, 'token': token}
        return Response(body, status=status.HTTP_201_CREATED)


class ActivationView(generics.GenericAPIView):
    """GET /api/activate/<uidb64>/<token>/ unlocks a new account.

    The frontend opens this route after the user clicked the mail link.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = ActivationSerializer

    def get(self, request, uidb64, token):
        """Activates the user behind a valid link."""
        data = {'uidb64': uidb64, 'token': token}
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            raise InvalidInput()
        activate_user(serializer.validated_data['user'])
        return Response({'message': 'Account successfully activated.'})


class LoginView(TokenObtainPairView):
    """POST /api/login/ checks the credentials and sets both JWT cookies."""

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainSerializer

    def post(self, request, *args, **kwargs):
        """Logs the user in, the tokens only travel as HttpOnly cookies."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            raise InvalidInput()
        user = serializer.user
        response = Response({
            'detail': 'Login successful',
            'user': {'id': user.id, 'username': user.username},
        })
        set_access_cookie(response, serializer.validated_data['access'])
        set_refresh_cookie(response, serializer.validated_data['refresh'])
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """POST /api/token/refresh/ issues a new access cookie.

    The refresh token comes from its cookie, the request body stays empty.
    A missing cookie ends in a 400, an invalid one in a 401.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        """Checks the refresh cookie and sets a fresh access cookie."""
        raw_token = request.COOKIES.get('refresh_token')
        if not raw_token:
            raise MissingRefreshToken()
        serializer = self.get_serializer(data={'refresh': raw_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as error:
            raise InvalidToken(error.args[0]) from error
        access = serializer.validated_data['access']
        response = Response({'detail': 'Token refreshed', 'access': access})
        set_access_cookie(response, access)
        return response


class LogoutView(APIView):
    """POST /api/logout/ blacklists the refresh token and clears cookies.

    Only the refresh cookie counts, an expired access cookie must not
    stop a user from logging out.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Logs the user out, the old refresh token is dead afterwards."""
        raw_token = request.COOKIES.get('refresh_token')
        if not raw_token:
            raise MissingRefreshToken()
        blacklist_refresh_token(raw_token)
        response = Response({
            'detail': 'Logout successful! All tokens will be deleted. '
                      'Refresh token is now invalid.'
        })
        delete_token_cookies(response)
        return response


class PasswordResetView(generics.GenericAPIView):
    """POST /api/password_reset/ sends a reset link by mail.

    The answer is the same whether an account exists or not.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = PasswordResetSerializer

    def post(self, request):
        """Queues the reset mail and answers with a fixed text."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            raise InvalidInput()
        request_password_reset(serializer.validated_data['email'])
        return Response({
            'detail': 'An email has been sent to reset your password.'
        })


class PasswordConfirmView(generics.GenericAPIView):
    """POST /api/password_confirm/<uidb64>/<token>/ sets a new password."""

    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = PasswordConfirmSerializer

    def post(self, request, uidb64, token):
        """Stores the new password for the user behind a valid link."""
        if not isinstance(request.data, dict):
            raise InvalidInput()
        data = {**request.data, 'uidb64': uidb64, 'token': token}
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            raise InvalidInput()
        reset_password(
            serializer.validated_data['user'],
            serializer.validated_data['new_password'],
        )
        return Response(
            {'detail': 'Your Password has been successfully reset.'}
        )
