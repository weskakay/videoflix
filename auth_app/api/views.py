from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from auth_app.api.exceptions import InvalidInput
from auth_app.api.serializers import RegistrationSerializer
from auth_app.services import register_user


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
