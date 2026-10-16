from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidInput(APIException):
    """General 400 that does not tell which field or account was wrong."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Please check your input and try again.'
    default_code = 'invalid_input'
