# using SendGrid's Python Library
from typing import Optional, Dict, Any
from pprint import pprint
from datetime import datetime
from pathlib import Path
import os


if not os.getenv("appwrite_end_point"):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


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
    
    
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def _build_email_template(
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

def send_email(
    app_name: str,
    to_email: str,
    name: str,
    lang: str
) -> Optional[Dict[str, Any]]:
    
    subject_code = 1
    subject = None
    if "-" in lang:
        decoded_lang = lang.split("-")
        lang = decoded_lang[0]
        subject_code = int(decoded_lang[1])

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


    # Define a dictionary mapping (subject_code, lang) -> subject
    SUBJECTS = {
        (1, "en"): "Verification Code",
        (1, "es"): "Código de verificación",
        (1, "fr"): "Code de vérification",
        (1, "pt"): "Código de verificação",
        (2, "en"): "Verification Link",
        (2, "es"): "Enlace de verificación",
        (2, "fr"): "Lien de vérification",
        (2, "pt"): "Link de verificação"
    }

    # Lookup subject with a fallback
    subject = SUBJECTS.get((subject_code, lang), "Subject")
# ----------------------------------

    code = cf.common_generate_payment_token(5)

    email_html = _build_email_template(
        button_fallback,
        this_msg_type,
        app_name,
        name,
        exp_msg,
        email_footer,
        footer_note,
        code=code["token"],
        expiration_minutes= 5
    )
    
    record = cf.common_get_record("email_server_data", app_name)
    
    if record:
        record = cf.common_decode_dict(record["data"]["data"])
        
    else:
        return {"success": False, "description": "No local Id"}
        


    message = Mail(
        from_email=record['username'],
        to_emails=to_email,
        subject=f"{app_name} {subject}",
        html_content=email_html)
    try:
        SGKey = os.environ.get('SENDGRID_API_KEY')
        sg = SendGridAPIClient(SGKey)
        response = sg.send(message)
        # print(response.status_code)
        # print(response.body)
        # print(response.headers)
        
        if int(response.status_code) == 202 :
            return {"success": True}
        else:
            return {"success": False, "description": "API problem"}
    except Exception as e:
        print(e.message)
    
    
if __name__ == "__main__":

    pprint(
            send_email(
                app_name="payNus",
                to_email="esteban.g.jandres@gmail.com",
                name=f"Esteban Jandres {cf.common_generate_int_id(2)}",
                lang="es-1"
            )
        )
    