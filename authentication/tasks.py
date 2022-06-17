from celery import shared_task
from django.conf import settings
from kavenegar import KavenegarAPI

from authentication.api.exceptions import OTPSendingException


@shared_task
def kavenegar_sms_task(receptor, token):
    try:
        api = KavenegarAPI(settings.SMS_API_KEY)
        params = {
            'template': settings.SMS_TEMPLATE_NAME,
            'receptor': receptor,
            'token': token
        }
        return str(api.verify_lookup(params))

    except:
        raise OTPSendingException()
