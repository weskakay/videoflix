from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from auth_app.api.exceptions import InvalidInput
from auth_app.api.serializers import (
    ActivationSerializer,
    RegistrationSerializer,
)
from auth_app.services import activate_user, register_user


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
