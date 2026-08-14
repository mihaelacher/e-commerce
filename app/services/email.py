from decimal import Decimal
from email.message import EmailMessage
import smtplib

from app.core.config import settings


def send_order_confirmation(
    recipient: str,
    order_id: int,
    total: Decimal,
) -> None:
    subject = f"Order #{order_id} confirmation"

    body = f"""
    Thank you for your order!

    Your order #{order_id} has been confirmed.

    Total: {total:.2f}

    We will process your order shortly.

    Thank you for shopping with us!
    """

    send_email(
        recipient=recipient,
        subject=subject,
        body=body,
    )


def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> None:
    message = EmailMessage()

    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
    ) as smtp:
        smtp.starttls()
        smtp.login(
            settings.smtp_username,
            settings.smtp_password,
        )
        smtp.send_message(message)
