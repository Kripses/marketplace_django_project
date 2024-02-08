from django.conf import settings
from django.core.mail import send_mail


def send_email(subject: str, message: str, address: str = '') -> None:
    recipients = [settings.DEFAULT_ADMIN_EMAIL]
    if address:
        recipients.append(address)

    if not address:
        return

    send_mail(
        subject=subject,
        from_email=settings.DEFAULT_FROM_EMAIL,
        message=message,
        recipient_list=[address],
    )
