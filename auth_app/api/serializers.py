from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


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
