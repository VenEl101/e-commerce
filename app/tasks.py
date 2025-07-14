from celery import shared_task
from django.core.mail import send_mail
from root import settings

@shared_task
def send_otp_email(email, code):
    print('123')
    subject = "Your Verification Code"
    message = f"Your verification code is: {code}"
    from_email = setting.EMAIL_HOSt_USER
    recipient_list = [email]

    return send_mail(subject, message, from_email, recipient_list)
