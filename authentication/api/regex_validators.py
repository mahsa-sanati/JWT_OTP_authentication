from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


mobile_format = r'^0\+?1?\d{10}$'
mobile_regex = RegexValidator(regex=mobile_format, message="Mobile number must be 11 digit")

username_format = r'^[a-z-0-9_.-]*$'

otp_format = r'^\+?1?\d{5}$'
