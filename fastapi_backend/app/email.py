import smtplib
from email.message import EmailMessage
from threading import Thread
from time import sleep

from . import config


def _send(msg: EmailMessage) -> bool:
    if not config.MAIL_SERVER:
        return False

    try:
        with smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT) as smtp:
            if config.MAIL_USE_TLS:
                smtp.starttls()
            if config.MAIL_USERNAME and config.MAIL_PASSWORD:
                smtp.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception:
        return False


def _send_async(msg: EmailMessage) -> None:
    if _send(msg):
        return

    sleep(10)
    _send(msg)


def send_email(subject: str, recipients: list[str], text_body: str, html_body: str | None = None) -> None:
    if not recipients:
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.MAIL_SENDER
    msg["To"] = ", ".join(recipients)
    msg.set_content(text_body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    Thread(target=_send_async, args=(msg,), daemon=True).start()
