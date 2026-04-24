from typing import Optional, Dict, Any
from pprint import pprint
import os


if not os.getenv("appwrite_end_point"):
    try:
        from dotenv import load_dotenv
    except ImportError:
        # dotenv is not installed; ignore when running in Appwrite Cloud
        load_dotenv = None

    # Load .env only if running locally
    import os

    if not os.getenv("APPWRITE_ENDPOINT") and load_dotenv:
        load_dotenv()  # loads variables from a local .env file


# ------------------------------
# Import Common Functions
# ------------------------------

try:
    from .. import common_functions as cf
except ImportError:

    import sys
    import os

    sys.path.append(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
    )

    import common_functions as cf


# ------------------------------
# Import Email Service
# ------------------------------

try:
    from .mail_service import EmailService
except ImportError:
    from mail_service import EmailService


APP_NAME: Optional[str] = None
MAILER_CACHE: Dict[str, "EmailService"] = {}


# ----------------------------------

def get_email_connection(app_name: str) -> Dict[str, Any]:

    global APP_NAME

    if APP_NAME != app_name:
        APP_NAME = app_name

    email_data = cf.common_get_record(
        "email_server_data",
        app_name
    )

    email_data_decoded = cf.common_decode_dict(
        email_data["data"]["data"]
    )

    return email_data_decoded


# ----------------------------------

def get_mailer(app_name: str) -> Optional["EmailService"]:

    global MAILER_CACHE

    if app_name in MAILER_CACHE:
        return MAILER_CACHE[app_name]

    email_data = get_email_connection(app_name)

    smtp_server = email_data.get("smtp_server")
    smtp_port = email_data.get("smtp_port")
    username = email_data.get("username")
    password = email_data.get("password")
    
    # print (smtp_server)

    if any(v is None for v in (smtp_server, smtp_port, username, password)):
        return None

    mailer = EmailService(
        smtp_server=smtp_server,
        smtp_port=int(smtp_port),
        username=username,
        password=password
    )

    MAILER_CACHE[app_name] = mailer

    return mailer


# ----------------------------------

def send_email(
    app_name: str,
    to_email: str,
    name: str,
    lang: str
) -> Optional[Dict[str, Any]]:

    mailer = get_mailer(app_name)

    if mailer is None:

        return {
            "error": True,
            "description": "Check your email connection details.",
            "code": 500
        }

    # ----------------------------------
    

    if lang == "en":

        exp_msg = "This code will expire in"
        email_footer = "If you did not request this code, you can safely ignore this email."
        footer_note = "This is an automated message, please do not reply."
        this_msg_type = "Your verification code:"
        subject = "Verification Code"
        button_fallback = "If the button does not work, copy and paste this link into your browser:"

    elif lang == "es":

        exp_msg = "Este código expirará en"
        email_footer = "Si no solicitó este código, puede ignorar este correo de forma segura."
        footer_note = "Este es un mensaje automático, por favor no responda."
        this_msg_type = "Su código de verificación:"
        subject = "Código de verificación"
        button_fallback = "Si el botón no funciona, copie y pegue este enlace en su navegador:"

    elif lang == "fr":

        exp_msg = "Ce code expirera dans"
        email_footer = "Si vous n'avez pas demandé ce code, vous pouvez ignorer cet e-mail en toute sécurité."
        footer_note = "Ceci est un message automatique, veuillez ne pas répondre."
        this_msg_type = "Votre code de vérification:"
        subject = "Code de vérification"
        button_fallback = "Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :"

    elif lang == "pt":

        exp_msg = "Este código expirará em"
        email_footer = "Se você não solicitou este código, pode ignorar este e-mail com segurança."
        footer_note = "Esta é uma mensagem automática, por favor não responda."
        this_msg_type = "Seu código de verificação:"
        subject = "Código de verificação"
        button_fallback = "Se o botão não funcionar, copie e cole este link no seu navegador:"

    else:

        return {
            "error": True,
            "description": "Language not supported.",
            "code": 500
        }

    # ----------------------------------

    code = cf.common_generate_payment_token(5)

    return mailer.send_verification_email(
        subject,
        button_fallback,
        this_msg_type,
        app_name,
        to_email,
        name,
        exp_msg,
        email_footer,
        footer_note,
        code=code["token"]
    )


# ----------------------------------

if __name__ == "__main__":

    # print (get_mailer("payNus"))

    pprint(
        send_email(
            app_name="payNus",
            to_email="test-vvwd6pmil@srv1.mail-tester.com",
            name=f"Esteban Jandres {cf.common_generate_int_id(2)}",
            lang="en"
        )
    )
