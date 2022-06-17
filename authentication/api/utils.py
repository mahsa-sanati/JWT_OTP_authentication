from django.conf import settings     
from better_profanity import profanity

from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings
from random import randrange
 
from authentication.tasks import kavenegar_sms_task
from .exceptions import (
    DirtyContentException,
    NoValidOTPException,
    IncorrectOTPException,
)

redis = settings.REDIS


def get_user_from_request(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    data = {'token': token}

    valid_data = VerifyJSONWebTokenSerializer().validate(data)
    user = valid_data['user']
    return user

 
def token_generator(user):
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)

    return token


def set_otp_in_redis(mobile, otp, expiration):
    redis.set(f'otp:{mobile}', otp, expiration)


def user_send_otp_code(mobile, expiration=2*60):
    otp = randrange(10000, 99999)
    kavenegar_sms_task.apply_async(args=[mobile, otp])
    set_otp_in_redis(mobile, otp, expiration)
    return True


def user_verify_otp(mobile, otp, set_again_in_redis=True, new_expiration=10*60):
    get_code = redis.get(f'otp:{mobile}')
    if get_code is None:
        raise NoValidOTPException
    if get_code != otp:
        raise IncorrectOTPException
    if set_again_in_redis:
        set_otp_in_redis(mobile, otp, expiration=new_expiration)


def delete_otp_from_redis(mobile):
    redis.delete(f'otp:{mobile}')


def check_dirty_content(dirty_content):
    profanity.load_censor_words()
    is_default_dirty_content = profanity.contains_profanity(dirty_content)
    if is_default_dirty_content:
        raise DirtyContentException()