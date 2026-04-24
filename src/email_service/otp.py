import secrets


def generate_otp(length=6):
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))
