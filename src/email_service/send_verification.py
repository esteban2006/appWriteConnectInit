from queue_manager import add_email_job
from otp import generate_otp
from rate_limit import can_send
from config import RATE_LIMIT_SECONDS


def send_verification(email, name):

    if not can_send(email, RATE_LIMIT_SECONDS):
        print("Rate limit reached")
        return

    otp = generate_otp()

    template = open("templates/verification.html").read()

    html = template.replace("{{name}}", name)\
                   .replace("{{code}}", otp)\
                   .replace("{{minutes}}", "5")

    add_email_job({
        "to": email,
        "subject": "PayNus Verification Code",
        "html": html
    })

    print("OTP generated:", otp)


# test call
send_verification(
    "esteban.g.jandres@email.com",
    "Esteban"
)
