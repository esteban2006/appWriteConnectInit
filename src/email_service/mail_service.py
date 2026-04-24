import smtplib
import os
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from datetime import datetime
from pathlib import Path


if not os.getenv("appwrite_end_point"):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


# ------------------------------
# Rate limit protection
# ------------------------------

EMAIL_RATE_LIMIT = 5  # emails per second
_last_sent_times = []
_rate_lock = threading.Lock()


def rate_limit():
    global _last_sent_times

    with _rate_lock:

        now = time.time()

        _last_sent_times = [
            t for t in _last_sent_times if now - t < 1
        ]

        if len(_last_sent_times) >= EMAIL_RATE_LIMIT:

            sleep_time = 1 - (now - _last_sent_times[0])

            if sleep_time > 0:
                time.sleep(sleep_time)

        _last_sent_times.append(time.time())


        if len(_last_sent_times) > 100:
            _last_sent_times = _last_sent_times[-50:]


# ------------------------------
# Email Service
# ------------------------------

class EmailService:

    def __init__(self, smtp_server, smtp_port, username, password):

        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

        self._server = None

    # ----------------------------------

    def _get_connection(self):
        """
        Reuse SMTP connection if possible.
        Reconnect automatically if connection died.
        """

        if self._server:

            try:
                status = self._server.noop()[0]

                if status == 250:
                    return self._server

            except Exception:
                pass

        self._server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
        self._server.login(self.username, self.password)

        return self._server

    # ----------------------------------

    def send_verification_email(
        self,
        subject,
        button_fallback,
        this_msg_type,
        app_name,
        to_email,
        name,
        exp_msg,
        email_footer,
        footer_note,
        code,
        expiration_minutes=5
    ):

        html = self._build_email_template(
            button_fallback,
            this_msg_type,
            app_name,
            name,
            exp_msg,
            email_footer,
            footer_note,
            code,
            expiration_minutes
        )

        # -------------------------
        # plain text fallback
        # -------------------------

        text = f"""
            Hello {name},

            {this_msg_type}

            {code}

            {exp_msg} {expiration_minutes} minutes.

            If you did not request this email, please ignore it.
            """

        msg = MIMEMultipart("alternative")

        msg["Subject"] = subject
        msg["From"] = self.username
        msg["To"] = to_email
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()
        msg["Reply-To"] = self.username
        msg["List-Unsubscribe"] = "<mailto:info@sistemasintegradosao.com?subject=unsubscribe>"
        msg["X-Mailer"] = f"{app_name}-mailer"
        msg["Return-Path"] = "info@sistemasintegradosao.com"
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        # -------------------------
        # rate limiter
        # -------------------------

        rate_limit()

        try:

            server = self._get_connection()

            result = server.sendmail(
                self.username,
                [to_email],
                msg.as_string()
            )

            print("SMTP RESULT:", result)


        except Exception as e:

            print("SMTP ERROR:", str(e))

            return {
                "error": True,
                "descriptions": str(e),
                "code": 500
            }

        return {
            "to": to_email,
            "name": name,
            "description": "Email sent.",
            "code": 200
        }

    # ----------------------------------

    def _build_email_template(
        self,
        button_fallback,
        this_msg_type,
        app_name,
        name,
        exp_msg,
        email_footer,
        footer_note,
        code,
        expiration_minutes
    ):

        year = datetime.now().year

        link = os.getenv("payNusLink")

        verification_link = None

        if app_name == "payNus":
            verification_link = f"{link}{code}"

        template_path = (
            Path(__file__).parent
            / "templates"
            / "email_verification.html"
        )

        html_template = template_path.read_text(
            encoding="utf-8"
        )

        return html_template.format(
            button_fallback=button_fallback,
            app_name=app_name,
            name=name,
            this_msg_type=this_msg_type,
            verification_link=verification_link,
            exp_msg=exp_msg,
            expiration_minutes=expiration_minutes,
            email_footer=email_footer,
            footer_note=footer_note,
            year=year
        )
