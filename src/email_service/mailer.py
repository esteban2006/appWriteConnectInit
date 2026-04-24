import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS


logging.basicConfig(
    filename="logs/email.log",
    level=logging.INFO
)


def send_email(to_email, subject, html):

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(html, "html"))

    try:

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        logging.info(f"Email sent to {to_email}")

    except Exception as e:

        logging.error(f"Email failed: {e}")
        raise
