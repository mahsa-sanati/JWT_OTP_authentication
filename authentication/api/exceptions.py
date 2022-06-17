from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException


class PermissionException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('no permission.')


class UserExistException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('user does not exist.')


class IncorrectMobileException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('incorrect mobile.')


class IncorrectPasswordException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('incorrect password.')


class OTPSendingException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('there is some problem with sending otp.')


class IncorrectMobileEmailUsernameException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('incorrect login information.')


class NotConfirmedPasswordException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('incorrect password2.')


class BlockedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('your account has been blocked.')


class NoValidOTPException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('invalid or expired otp code.')


class IncorrectOTPException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('incorrect otp code.')


class DirtyContentException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('not proper content.')
