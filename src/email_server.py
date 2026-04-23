import jwt  # Assuming you're using PyJWT
from http import server
import smtplib
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_templates import *
from pprint import pprint


env_loaded = os.getenv("tron_api_one")


if env_loaded is None:
    # Define the path to your .env file (one directory up)
    env_file_path = '.env'

    # Open the file and read it
    with open(env_file_path, 'r') as file:
        for line in file:
            # Skip empty lines and lines starting with # (comments)
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                # Set the environment variable
                os.environ[key] = value


class EmailSender:
    def __init__(self,
                 from_email,
                 smtp_server,
                 smtp_port,
                 smtp_user,
                 smtp_password):

        self.from_email = from_email
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.server = None
        self.mins_to_exp = int(os.getenv("reset_password_exp_time"))
        self._connect()

    def get_millis(self):
        """
        Get the current time in milliseconds since the Unix epoch.

        Returns:
        - int: Current time in milliseconds.
        """
        return int(time.time() * 1000)

    def create_reset_password_token(self, email=None):
        """
        Create a JWT that expires 3 minutes from the current time.

        Returns:
        - str: The encoded JWT.
        """

        secret_key = os.getenv("secret_jwt")
        current_millis = self.get_millis()
        three_minutes_ms = self.mins_to_exp * 60 * 1000
        exp_millis = current_millis + three_minutes_ms

        payload = {
            'exp': exp_millis,
            "email": email.get("to", "")[0]
        }

        # PyJWT expects 'exp' in seconds, not milliseconds
        payload['exp'] //= 1000

        token = jwt.encode(payload, secret_key, algorithm='HS256')
        return token

    def decode_password_reset_link(self, token):

        secret = os.getenv("secret_jwt")

        print(f"we got secret ---->")

        try:
            return jwt.decode(token, secret, algorithms=["HS256"])

        except jwt.ExpiredSignatureError:
            return "expired"

    def _connect(self):
        """Establish SMTP connection"""
        try:
            self.server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            self.server.login(self.smtp_user, self.smtp_password)
            print("SMTP connection established")
        except Exception as e:
            print(f"Connection error: {e}")
            self.server = None
            raise

    def _ensure_connection(self):
        """Verify and reconnect if needed"""
        try:
            if self.server is None:
                self._connect()
            # Check if connection is still alive
            self.server.noop()
        except:
            # If noop fails, reconnect
            self._connect()

    def close(self):
        """Close the SMTP connection"""
        if self.server:
            try:
                self.server.quit()
            except:
                pass
            finally:
                self.server = None

    def __del__(self):
        """Destructor to clean up connection"""
        self.close()

    def get_email_body(self, name=None):
        if name is None:
            return "select an email template "

        if name == "reset_password_email":
            return reset_password_email

        elif name == "one_email_template":
            return one_email_template

        else:
            return

    def send_email(self,
                   to_emails=[],
                   bcc_emails=[],
                   subject="Conoce en la fase que nos encontramos en Proyecto One",
                   body=None):
        if not body:
            return False

        is_html = True
        self._ensure_connection()

        # Create the email message
        message = MIMEMultipart()
        message["From"] = self.from_email

        if to_emails:
            message["To"] = ", ".join(to_emails)

        message["Subject"] = subject

        # Combine to and bcc for the actual sending
        all_recipients = to_emails + bcc_emails

        # Attach the body
        message.attach(MIMEText(body, "html" if is_html else "plain"))

        # Send the email
        try:
            self.server.sendmail(
                self.from_email, all_recipients, message.as_string())
            return True
        except Exception as e:
            print(f"Send error: {e}")
            # Try to reconnect once if send fails
            try:
                self._connect()
                self.server.sendmail(
                    self.from_email, all_recipients, message.as_string())
                return True
            except Exception as retry_e:
                print(f"Retry failed: {retry_e}")
                return False


def get_sender(my_sender=None):

    if my_sender is None:
        return None

    elif my_sender == "mano_a_mano":
        # Create sender with persistent connection
        # todo remember to add this to the env file
        sender = EmailSender(
            from_email=os.getenv("mam_smtp_user"),
            smtp_server=os.getenv("mam_smtp_server"),
            smtp_port=os.getenv("mam_smtp_port"),
            smtp_user=os.getenv("mam_smtp_user"),
            smtp_password=os.getenv("mam_smtp_password")
        )
        return sender

    elif my_sender == "one":
        # Create sender with persistent connection
        sender = EmailSender(
            from_email=os.getenv("one_smtp_user"),
            smtp_server=os.getenv("one_smtp_server"),
            smtp_port=os.getenv("one_smtp_port"),
            smtp_user=os.getenv("one_smtp_user"),
            smtp_password=os.getenv("one_smtp_password")
        )
        return sender


def send_email(recepients_body, email_body, subject, replacements={}, my_sender=None):

    sender = get_sender(my_sender)

    if sender is None:
        return "no sender provided"

    if "Reset Password" in subject:
        reset_password_token = sender.create_reset_password_token(
            recepients_body)

        replacements["EmailBody"] = (
            f"Click the following link "
            f"to reset your password: <a href='/resetPassword?token={reset_password_token}' target='_blank'>Reset Password</a> "
            f"valid for {sender.mins_to_exp} minutes"
        )

        print(f"reset link {reset_password_token}")

    # Get the email body template
    body = sender.get_email_body(email_body)

    if "select an email template" in body:
        return body

    # Apply replacements if any
    if replacements:
        for key, value in replacements.items():
            body = body.replace(key, value)

    # print(f"\n\n{body}\n\n")

    result = sender.send_email(
        to_emails=recepients_body["to"],
        bcc_emails=recepients_body["bcc"],
        subject=subject,
        body=body
    )
    print(f"Email to {recepients_body['to']} sent: {result}")

    # Explicitly close when done (optional - will be called automatically when object is destroyed)
    sender.close()

    if result:
        return "Email sent successfully"


def get_manager_ia_token_decoded(token):
    sender = get_sender("one")

    decoded_token = sender.decode_password_reset_link(token)

    sender.close()

    if "expired" in decoded_token:
        return False
    else:
        return decoded_token


if __name__ == "__main__":
    pass
    # print()
    # print("----------->")
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDQzMzgyNjgsImVtYWlsIjp7ImJjYyI6W10sInRvIjpbImVzdGViYW4uZy5qYW5kcmVzQGdtYWlsLmNvbSJdfX0.gnWMErpcKKZmkRkYrfc3Tp7-jBPZYcX7pSdc5tKe0bY)."
    # print(get_manager_ia_token_decoded(token))
    # https://docs.google.com/document/d/1EXSab1JPgNWbtvj0y_nSyQ047IO0Q8r3ZKvb6bQvV7I/edit?tab=t.0
    # https://docs.google.com/document/d/1neXxIO6DZxdhP1Qy8QMlybKTkBXCJryMQczwE3c6E4E/edit?tab =t.0
