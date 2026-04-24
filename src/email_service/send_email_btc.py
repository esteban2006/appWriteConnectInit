import requests
import os
from pathlib import Path
from datetime import datetime

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

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    import common_functions as cf


import os
from pathlib import Path
from datetime import datetime
import requests


def sendEmailBtc(
    _from: str = "tlovendo",
    to: str = "",
    subject: str = "email_verification",
    lang: str = "en",
    data: dict = None,
    test: bool = True,
):
    """
    Sends transactional HTML emails using the SivarWallet email API.

    This function renders an HTML email template and injects translated
    text depending on the requested language and email type.

    Supported Email Types
    ---------------------
    email_verification
        Sends an account verification email containing a secure
        verification token and expiration time.

    email_order
        Sends an order confirmation email containing a link
        to view the order and a secret access code.

    Parameters
    ----------
    _from : str
        Application identifier sending the email.
        Examples: "tlovendo", "payNus".

    to : str
        Recipient email address.

    subject : str
        Email template identifier.

        Supported values:
        - "email_verification"
        - "email_order"

    lang : str
        Language code for translation.

        Supported:
        - "en"
        - "es"
        - "fr"
        - "pt"

    data : dict
        Dynamic values injected into the email template.

        Required keys:
        - app_name
        - name
        - expiration_minutes
        - theme

        Optional keys:
        - order_id

    test : bool
        If True, prints the generated HTML instead of sending the email.

    Environment Variables
    ---------------------
    btcAccess
        Authorization token for API access.

    tlovendoStoreId
        Store ID used for verification emails.

    payNusStoreId
        Store ID used for order emails.
    """

    if not data:
        return {"error": True, "description": "Missing data"}

    if lang not in ["en", "es", "fr", "pt"]:
        return {"error": True, "description": "Language not supported"}

    btcAccess = os.getenv("btcAccess")

    # ------------------------------------------------------------------
    # TRANSLATIONS
    # ------------------------------------------------------------------

    TRANSLATIONS = {
        "email_verification": {
            "en": {
                "subject": "Verification Link",
                "this_msg_type": "Please click the button to verify your account.",
                "exp_msg": "This code will expire in",
                "email_footer": "If you did not request this code, you can safely ignore this email.",
                "footer_note": "This is an automated message, please do not reply.",
                "button_fallback": "If the button does not work, copy and paste this link into your browser:",
                "btn_name": "Click to confirm your account",
            },
            "es": {
                "subject": "Link de verificación",
                "this_msg_type": "Por favor haga clic en el botón para verificar su cuenta.",
                "exp_msg": "Este código expirará en",
                "email_footer": "Si no solicitó este código, puede ignorar este correo de forma segura.",
                "footer_note": "Este es un mensaje automático, por favor no responda.",
                "button_fallback": "Si el botón no funciona, copie y pegue este enlace en su navegador:",
                "btn_name": "Confirmar su cuenta",
            },
            "fr": {
                "subject": "Lien de vérification",
                "this_msg_type": "Veuillez cliquer sur le bouton pour vérifier votre compte.",
                "exp_msg": "Ce code expirera dans",
                "email_footer": "Si vous n'avez pas demandé ce code, vous pouvez ignorer cet e-mail en toute sécurité.",
                "footer_note": "Ceci est un message automatique, veuillez ne pas répondre.",
                "button_fallback": "Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :",
                "btn_name": "Confirmer votre compte",
            },
            "pt": {
                "subject": "Link de verificação",
                "this_msg_type": "Por favor clique no botão para verificar sua conta.",
                "exp_msg": "Este código expirará em",
                "email_footer": "Se você não solicitou este código, pode ignorar este e-mail com segurança.",
                "footer_note": "Esta é uma mensagem automática, por favor não responda.",
                "button_fallback": "Se o botão não funcionar, copie e cole este link no seu navegador:",
                "btn_name": "Confirmar sua conta",
            },
        },
        "email_order": {
            "en": {
                "subject": "Order confirmation",
                "this_msg_type": "Please click the button to verify the status of your order.",
                "email_footer": "Your order will be processed within 48 hours.",
                "footer_note": "This is an automated message, please do not reply.",
                "button_fallback": "If the button does not work, copy and paste this link into your browser:",
                "btn_name": "Go to your order",
                "secret_code_msg": "To open your order you will need this code.",
            },
            "es": {
                "subject": "Confirmación de pedido",
                "this_msg_type": "Por favor haga clic en el botón para verificar el estado de su pedido.",
                "email_footer": "Su pedido será procesado dentro de 48 horas.",
                "footer_note": "Este es un mensaje automático, por favor no responda.",
                "button_fallback": "Si el botón no funciona, copie y pegue este enlace en su navegador:",
                "btn_name": "Ver su pedido",
                "secret_code_msg": "Para abrir su pedido necesitará este código.",
            },
            "fr": {
                "subject": "Confirmation de commande",
                "this_msg_type": "Veuillez cliquer sur le bouton pour vérifier l'état de votre commande.",
                "email_footer": "Votre commande sera traitée dans un délai de 48 heures.",
                "footer_note": "Ceci est un message automatique, veuillez ne pas répondre.",
                "button_fallback": "Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :",
                "btn_name": "Voir votre commande",
                "secret_code_msg": "Pour ouvrir votre commande vous aurez besoin de ce code.",
            },
            "pt": {
                "subject": "Confirmação do pedido",
                "this_msg_type": "Por favor clique no botão para verificar o status do seu pedido.",
                "email_footer": "Seu pedido será processado dentro de 48 horas.",
                "footer_note": "Esta é uma mensagem automática, por favor não responda.",
                "button_fallback": "Se o botão não funcionar, copie e cole este link no seu navegador:",
                "btn_name": "Ver seu pedido",
                "secret_code_msg": "Para abrir seu pedido você precisará deste código.",
            },
        },
    }

    t = TRANSLATIONS.get(subject, {}).get(lang)

    if not t:
        return {"error": True, "description": "Translation not found"}

    confirmation_link = None
    token = None
    target = None

    # ------------------------------------------------------------------
    # EMAIL TYPE LOGIC
    # ------------------------------------------------------------------

    if subject == "email_verification":

        target = os.getenv("tlovendoStoreId")

        token = cf.common_generate_payment_token(int(data["expiration_minutes"]))

        confirmation_link = (
            f"https://tlovendosv.com/ac.html/?account={to}&token={token['token']}"
        )

    elif subject == "email_order":

        target = os.getenv("payNusStoreId")

        token = cf.common_generate_payment_token(4320)

        confirmation_link = (
            f"https://tlovendosv.com/order.html/?order={data['order_id']}"
        )

    # ------------------------------------------------------------------
    # TEMPLATE
    # ------------------------------------------------------------------

    template_path = Path(__file__).parent / "templates" / f"{subject}.html"

    html_template = template_path.read_text(encoding="utf-8")

    theme = data["theme"]

    html_template = html_template.format(
        app_name=data["app_name"],
        name=data["name"],
        verification_link=confirmation_link,
        expiration_minutes=data.get("expiration_minutes"),
        year=datetime.now().year,
        token=token["token"] if token else "",
        top_color=f'<td align="center" style="background:{theme}; padding:30px;">',
        btn_color=f'<td align="center" bgcolor="{theme}" style="border-radius:6px;">',
        link_color=f'<a href="{confirmation_link}" style="color:{theme}; word-break:break-all;">',
        **t,
    )

    if not target:
        return {"error": True, "description": "Store ID not configured"}

    url = f"https://sivarwallet.sistemasintegradosao.com/api/v1/stores/{target}/email/send"

    payload = {
        "email": to,
        "subject": t["subject"],
        "body": html_template,
    }

    headers = {
        "content-type": "application/json",
        "authorization": f"Basic {btcAccess}",
    }

    if test:
        print(html_template)
        return

    response = requests.post(url, json=payload, headers=headers)

    print("Status:", response.status_code)
    print("Response:", response.text)


if __name__ == "__main__":
    pass

    # app_name enum : tlovendo, payNus
    # subject enum : email_verification, email_order

    # sendEmailBtc(
    #     _from="tlovendo",
    #     to="esteban.g.jandres@gmail.com",
    #     subject="email_order",
    #     lang="es",
    #     data={
    #         "app_name": "tlovendo",
    #         "name": "Esteban Jandres",
    #         "expiration_minutes": 5,
    #         "theme": "#ff8f9c",
    #         "order_id": cf.common_generate_int_id(6),
    #     },
    #     test=True,
    # )
