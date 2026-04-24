import os


SMTP_SERVER = "mail.sistemasintegradosao.com"
SMTP_PORT = 465
SMTP_USER = "info@sistemasintegradosao.com"
SMTP_PASS = os.getenv("SMTP_PASS")

MAX_RETRIES = 3
RATE_LIMIT_SECONDS = 60
