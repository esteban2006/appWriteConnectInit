import requests, re, json, random, string
from pprint import pprint
from datetime import datetime, timedelta, timezone
from appwrite.client import Client
from appwrite.services.databases import Databases  # Import the Databases class
from appwrite.services.account import Account
from appwrite.exception import AppwriteException


# email handling system
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

# jwt token
import jwt


app_key = "standard_c8ed384c3b34a4e773445f193b369cf997fce6a27888f31c6d3fc88fe5f98dce43da0b70024e1a022faab44c0f0ff86e4367e4ced303dca8d00826d9a63379168c95a083bb3028c8da9f48c2192ee08e57356453271b1bf7b413288cba1aa53bf65edd1841326c52777b70db2152b32d113c0cfef76c90ac2c3860cd3c52d963"
client = Client()
client.set_endpoint("https://cloud.appwrite.io/v1")  # Your API Endpoint
client.set_project("unit-333")  # Your project ID
client.set_key(app_key)  # Your secret API key
db_id = "66d68aff00057628676d"
users = "66d691ef001811e67511"
citas = "66d72bfa00381c7dcc73"
history = "66dc8b0a0016d196a40c"
emails_sent_collection = "673a95c000339fac06da"

databases = Databases(client)
data = {
    "name": "name",
    "phone_number": "phone",
    "address": "address",
    "local_id": "dui",
    "id": "id",
    "current_visit": "{}",
    "all_visits": "{}",
    "signature_form": "{}",
}


########################################################################################################################################
###### one  ############################################################################################################################
########################################################################################################################################


def get_current_month_id():
    """
    Returns the ID of the current month as an integer (1 for January, 12 for December).
    """
    return datetime.now().month


def one_create_document(db_id="xxx", collection="xxx", document_id="test", data={}):

    print("creating one document")
    print(f"db_id {db_id} collection {collection} document_id {document_id} ")

    result = databases.create_document(
        database_id=db_id,
        collection_id=collection,
        document_id=document_id,
        data=data,
    )
    # Remove any keys starting with '$' or if the key is 'all_visits'
    if isinstance(result, dict):
        return {"created": True}

    return result


def create_one_uid(length=32):
    """Generates a valid Appwrite document ID."""
    characters = string.ascii_letters + string.digits + "_"
    return "ONE_" + "".join(random.choice(characters) for i in range(length))


def create_one_user(email="email@example.com", password="asdfasdf"):
    """Creates a new user in appwrite db

    Args:
        email (str, optional): _description_. Defaults to "email@example.com".
        password (str, optional): _description_. Defaults to "asdfasdf".

    Returns:
        _type_: bool
    """

    myUid = create_one_uid()  # Assuming create_one_uid() is defined elsewhere
    account = Account(client)

    try:
        result = account.create(user_id=myUid, email=email, password=password)
        return {"msg": True}

    except AppwriteException as e:
        return {"msg": e.message}


def get_one_account(email="email@example.com", password="asdfasdf"):
    try:
        account = Account(client)
        result = account.create_email_password_session(email, password)
        return {"msg": True}

    except AppwriteException as e:
        return {"msg": e.message}


def get_password_reset(email="estebs@gmail.com", url="https://cloud.appwrite.io/reset"):
    """
    {
        '$createdAt': '2024-11-13T04:58:28.565+00:00',
        '$id': '673431f489e089a4093d',
        'expire': '2024-11-13T05:58:28.564+00:00',
        'phrase': '',
        'secret': '35fbe0f6f30efb3bda3ab7e11d7c123faa0ee2d6510f7dca86bc3c1e245b9aa00f4c484c650aeca1f208782c825c1c9614bfa383a340cc4ccf5073b26fad45375af06804faf65fa8b41b361edd2644d973614e7a609ef22efa100e5ffe3466ba2e884bfe1195e94e405b669b1684cf71cd8783b6223c4d11fd68d083dbfeb5cf',
        'userId': 'ONE_rj68xi0jwUfsIOpAkPtVStGiBcgbV6sS'
     }

    Returns:
        _type_: _description_
    """
    try:
        account = Account(client)  # Ensure `client` is properly configured for Appwrite
        # `url` must be a valid Appwrite-allowed URL for redirection
        result = account.create_recovery(email, url)
        # pprint(result)
        return result

    except AppwriteException as e:
        # Capture and display error message if URL is invalid or other error occurs
        return {"msg": e.message}


def reset_password(email, password):

    data = get_password_reset(email)

    try:
        account = Account(client)

        result = account.update_recovery(
            user_id=data["userId"], secret=data["secret"], password=password
        )
        return True
    except AppwriteException as e:
        # Capture and display error message if URL is invalid or other error occurs
        return False


def generate_password_change_token(password):
    # Set the expiration time to 2 minutes from now
    expiration_time = datetime.now(tz=timezone.utc) + timedelta(minutes=2)
    return jwt.encode(
        {"token": password, "exp": expiration_time},
        f"On3_{password*3}",
        algorithm="HS256",
    )


def verify_token(token, secret="test", reset=False, email="test"):

    if not reset:
        try:
            return jwt.decode(token, f"On3_{secret*3}", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return "expired"
    else:
        try:
            is_valid_token = jwt.decode(token, f"On3_{secret*3}", algorithms=["HS256"])
            is_valid_token["email"] = email
            is_valid_token["is_valid_token"] = True
            reset_password(email, secret)
            return {"is_valid_token": is_valid_token}
        except jwt.ExpiredSignatureError:
            return "expired"


def get_html_email_with_token():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
        <style>
            /* This style will be applied to the entire email */
            body {
                font-family: 'Roboto', sans-serif;
                margin: 0;
                padding: 0;
                text-align: center;
            }

            /* Styles for the table container */
            .container {
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
            }

            /* Button styles for email */
            .button {
                background-color: #858C3B;
                color: white;
                text-decoration: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
                display: inline-block;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="container">
            <tr>
                <td>
                    <h1 style="color: #858C3B; margin-bottom: 20px;">{{title}}</h1>
                    <img 
                        src="https://onemultinversiones.com/assets/img/LOGOS_/base_logo_transparent_background.png" 
                        alt="Image" 
                        style="width: 256px; height: 126px; margin: 20px 0;">
                    
                        <p>
                            {{message}}
                        </p>

                    <!-- Button styled as a link -->
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin: 20px auto;">
                        <tr>
                            <td align="center">
                                <a href="{{link}}" target="_blank" class="button">
                                    {{Ingresar ahora}}
                                </a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>

    """


def modify_html_email_with_token(email: str, password: str, lang: str) -> str:
    """
    Modifies specific lines in the HTML template and returns the modified content as a string.

    Args:
        email (str): The email to insert into the HTML file.
        password (str): The password to insert into the HTML file.
        link (str): The link to insert into the HTML file.

    Returns:
        str: The modified HTML content as a string.
    """
    link = "https://onemultinversiones.com/timeLine/confirm-password.html?"
    message = None
    loginNow = None
    if lang == "en":
        message = "To change your password, please click on the confirm password button and confirm the password you want to assign."
        loginNow = "Confirm new password"
        title = "Password change confirmation"

    elif lang == "es":
        message = "Para cambiar su contraseña, haga clic en el botón confirmar contraseña y confirme la contraseña que desea asignar."
        loginNow = "Confirma tu nueva clave"
        title = "Confirmacion de cambio de clave"

    else:

        message = "To change your password, please click on the confirm password button and confirm the password you want to assign."
        loginNow = "Confirm new password"
        title = "Password change confirmation"
    try:
        html_content = get_html_email_with_token()
        token = generate_password_change_token(password)
        link = f"{link}email={email}&key={token}"
        # Replace placeholders with actual content
        modified_content = (
            html_content.replace("{{message}}", message)
            .replace("{{link}}", link)
            .replace("{{Ingresar ahora}}", loginNow)
            .replace("{{title}}", title)
        )
        return modified_content
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""


def send_email(to_emails: str, lang: str = "en", password: str = "123123123") -> None:
    """
    Sends an email using an SMTP server.

    Args:
        smtp_server (str): The SMTP server address.
        smtp_port (int): The port to use for the SMTP server.
        smtp_user (str): The username to authenticate with the SMTP server.
        smtp_password (str): The password to authenticate with the SMTP server.
        from_email (str): The sender's email address.
        to_emails (List[str]): A list of recipient email addresses.
        subject (str): The subject of the email.
        body (str): The body text of the email.
        is_html (bool): Whether the body is HTML content. Defaults to False.
    """

    update_one_emails_sent()

    smtp_server = "mail.onemultinversiones.com"
    smtp_port = 465
    smtp_user = "info@onemultinversiones.com"
    smtp_password = "597925080754084"
    from_email = "info@onemultinversiones.com"
    to_emails = [to_emails]
    subject = "ONE multinversiones"
    body = modify_html_email_with_token(to_emails[0], password, lang)
    is_html = True

    # Create the email message
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = ", ".join(to_emails)
    message["Subject"] = subject

    # Attach the body as HTML or plain text
    if is_html:
        message.attach(MIMEText(body, "html"))  # Correctly mark the body as HTML
    else:
        message.attach(MIMEText(body, "plain"))

    # Connect to the SMTP server and send the email
    try:
        # Use SMTP_SSL for port 465
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        # server.set_debuglevel(1)  # Enable debug mode
        # Login to the SMTP server
        server.login(smtp_user, smtp_password)
        # Send the email
        server.sendmail(from_email, to_emails, message.as_string())
    except Exception as e:
        print(f"An error occurred: {e}")
        # Include SMTP debug information
        if hasattr(server, "ehlo_resp"):
            print(f"SMTP Response: {server.ehlo_resp}")
        if hasattr(server, "last_helo_resp"):
            print(f"Last HELO Response: {server.last_helo_resp}")

    finally:
        server.quit()
        return True


def update_one_emails_sent():
    # Fetch the document
    document = databases.get_document(
        database_id=db_id,
        collection_id=emails_sent_collection,
        document_id="one_enviados",
    )

    # Ensure the data is loaded as a dictionary
    data = json.loads(document["data"])  # Convert JSON string to Python dictionary

    # Get current month ID
    target = str(get_current_month_id())

    # Update the value for the current month
    current_target_value = data.get(target, 0) + 1
    data[target] = current_target_value

    # Update the document with the modified data
    databases.update_document(
        database_id=db_id,
        collection_id=emails_sent_collection,
        document_id="one_enviados",
        data={"data": json.dumps(data)},  # Pass as a dictionary, not a JSON string
    )


########################################################################################################################################
##### termovida  #######################################################################################################################
########################################################################################################################################


def is_key_valid(key):
    """Checks if a key is a valid substring of the original string, handling wraparound.

    Args:
        original_string: The original string.
        key: The key to check.
        start_index: The starting index to check from.

    Returns:
        True if the key is valid, False otherwise.
    """

    if "_" not in key:
        return False

    original_string = app_key

    key, start_index = key.split("_")
    start_index = int(start_index)

    # Handle wraparound
    key_length = len(key)
    key_chars = []
    for i in range(key_length):
        key_chars.append(original_string[(start_index + i) % len(original_string)])

    return "".join(key_chars) == key


def get_collection(collection=users):
    if collection == users:
        return users
    elif collection == citas:
        return citas
    elif collection == history:
        return history
    elif collection == "users":
        return users
    elif collection == "citas":
        return citas
    elif collection == "history":
        return history
    else:
        return


def create_document(collection=users, document_id="test", data={}):

    collection = get_collection(collection)

    result = databases.create_document(
        database_id=db_id,
        collection_id=collection,
        document_id=document_id,
        data=data,
    )
    # Remove any keys starting with '$' or if the key is 'all_visits'
    if isinstance(result, dict):
        return {"created": True}

    return result


def get_document(collection=users, document_id="test"):

    collection = get_collection(collection)
    try:
        # Fetch the document

        result = databases.get_document(
            database_id=db_id,
            collection_id=collection,
            document_id=document_id,
        )

        # Remove any keys starting with '$' or if the key is 'all_visits'
        if isinstance(result, dict):
            result = {
                key: value
                for key, value in result.items()
                if not key.startswith("$") and key != "all_visits"
            }

        return result

    except Exception as e:
        return "Document with the requested ID could not be found."


def get_all_visits(collection="users", document_id="test"):

    collection = get_collection(collection)
    try:
        # Fetch the document
        result = databases.get_document(
            database_id=db_id,
            collection_id=collection,
            document_id=document_id,
        )

        # Remove any keys starting with '$' or if the key is 'all_visits'
        if isinstance(result, dict):
            result = {
                key: value
                for key, value in result.items()
                if not key.startswith("$") and key == "all_visits"
            }

        return result

    except Exception as e:
        return "Document with the requested ID could not be found."


def update_documents(collection="users", document_id="test", data_to_update={}):

    collection = get_collection(collection)
    print("\ndata to update ... from history")
    print(f"collection ... {collection}")
    print(f"document_id ... {document_id}")
    pprint(data_to_update)
    result = databases.update_document(
        database_id=db_id,
        collection_id=collection,
        document_id=document_id,
        data=data_to_update,
    )
    return result


def update_history(document_id="test", data_to_update={}):

    # Fetch the current history document
    current_history = get_document(history, document_id)

    # If the document does not exist, create a new one
    if current_history == "Document with the requested ID could not be found.":
        data_to_update = {"history": json.dumps([data_to_update]), "archive": "[]"}
        return create_document(history, document_id, data_to_update)
    else:
        # Get the current history and check its type
        current_history_data = current_history["history"]
        if isinstance(current_history_data, str):
            # If it's a JSON string, parse it
            current_history = json.loads(current_history_data)
        elif isinstance(current_history_data, list):
            # If it's already a list, use it directly
            current_history = current_history_data
        else:
            # If it's in an unexpected format, raise an error
            raise ValueError(
                f"Unexpected format for history: {type(current_history_data)}"
            )

        # Prepare the new full history
        full_history = [
            json.loads(h_log) if isinstance(h_log, str) else h_log
            for h_log in current_history
        ]
        full_history.append(data_to_update)

        # Update the document data
        data_to_update = {"history": json.dumps(full_history), "archive": "[]"}
        print("\nData to update in history ")
        pprint(data_to_update)

        # Update the document in the database
        databases.update_document(
            database_id=db_id,
            collection_id=history,
            document_id=document_id,
            data=data_to_update,
        )

        return full_history


# print (create_document('users', 'new_test', data))
# print (update_document())
# pprint (get_document())
# print(is_key_valid("tanda_1"))
# print(create_one_uid())
