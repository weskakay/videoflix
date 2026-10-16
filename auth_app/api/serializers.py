from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from auth_app.utils import find_user_by_uid


class RegistrationSerializer(serializers.ModelSerializer):
    """Checks the sign-up data, the account itself is created elsewhere."""

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'email': {'required': True, 'max_length': 150},
            'password': {'write_only': True},
        }

    def validate_email(self, value):
        """Lowercases the address and rejects one that is already taken."""
        email = value.lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('Email is already in use.')
        return email

    def validate(self, data):
        """Checks that both passwords match and are strong enough."""
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError('Passwords do not match.')
        user = User(username=data['email'], email=data['email'])
        validate_password(data['password'], user)
        return data


class ActivationSerializer(serializers.ModelSerializer):
    """Turns the uid and token from a mail link into the matching user."""

    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['uidb64', 'token']

    def validate(self, data):
        """Rejects a link with an unknown user or a wrong or old token."""
        user = find_user_by_uid(data['uidb64'])
        token = data['token']
        if not user or not default_token_generator.check_token(user, token):
            raise serializers.ValidationError('Invalid link.')
        data['user'] = user
        return data


class EmailTokenObtainSerializer(TokenObtainPairSerializer):
    """Logs in with email and password instead of the username."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        """Drops the username field the parent class adds."""
        super().__init__(*args, **kwargs)
        self.fields.pop('username')

    def validate(self, attrs):
        """Refuses unknown emails, wrong passwords and inactive users."""
        user = User.objects.filter(email__iexact=attrs['email']).first()
        password = attrs['password']
        if not user or not user.is_active:
            raise serializers.ValidationError('Invalid credentials.')
        if not user.check_password(password):
            raise serializers.ValidationError('Invalid credentials.')
        credentials = {'username': user.username, 'password': password}
        return super().validate(credentials)


class PasswordResetSerializer(serializers.ModelSerializer):
    """Checks the email for a reset request, existing or not."""

    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['email']


class PasswordConfirmSerializer(ActivationSerializer):
    """Checks the reset link like the activation link, plus the passwords."""

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta(ActivationSerializer.Meta):
        fields = ['uidb64', 'token', 'new_password', 'confirm_password']

    def validate(self, data):
        """Rejects a bad link, different passwords or a weak password."""
        data = super().validate(data)
        if not data['user'].is_active:
            raise serializers.ValidationError('Account is not active.')
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError('Passwords do not match.')
        validate_password(data['new_password'], data['user'])
        return data
