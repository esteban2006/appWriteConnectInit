import smtplib, csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List


def html_body():
    return """

<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Carta Informativa - Proyecto ONE</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        line-height: 1.6;
        margin: 0;
        padding: 0;
        background-color: #f9f9f9;
        color: #333
      }

      .container {
        max-width: 800px;
        margin: 30px auto;
        background: #fff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, .1)
      }

      h1 {
        text-align: center;
        color: #444
      }

      p {
        margin: 10px 0
      }

      ul {
        margin: 10px 0 20px 20px;
        list-style-type: disc
      }

      .signature {
        margin-top: 40px;
        text-align: center
      }

      .signature-line {
        margin-top: 10px;
        border-top: 1px solid #333;
        width: 300px;
        margin-left: auto;
        margin-right: auto
      }

      .contact-info {
        margin-top: 30px;
        font-size: .9em;
        color: #666
      }

      .highlight {
        color: #d9534f;
        font-weight: 700
      }

      a {
        color: #0275d8;
        text-decoration: none
      }

      a:hover {
        text-decoration: underline
      }
    </style>
  </head>
  <body>
    <div class="container">
      <img src="{{company_logo}}" alt="Image" style="width:256px;height:256px;margin:20px 0">
      {{new_message}}
    </div>
  </body>
</html>

"""


def get_logo(logo="logo_one"):

    if logo == "logo_one":
        return (
            "https://onemultinversiones.com/assets/img/LOGOS_/Logo_Fondo%20Blanco.png"
        )


def get_message(msg="one_two"):
    if msg == "one_two":
        return """

    <h1>Santa Tecla, 20 de Enero del 2025</h1>Estimados clientes, 
      <p>Espero que estén teniendo un excelente inicio de año. A través de este medio, les recordamos que, si alguno de ustedes requiere el comprobante de algún depósito, pueden comunicarse con nosotros al número 6024-7030. Asimismo, les solicitamos enviar el comprobante de cada depósito realizado a ese mismo número.</p>
      <p>Quedamos a su disposición para cualquier consulta.</p>
      <p>Atentamente, Multi Inversiones One</p>
      
      """


def send_email(
    to_emails: List[str], name: str = "name", logo=None, message=None, testing=True
) -> None:
    smtp_server = "mail.onemultinversiones.com"
    smtp_port = 465
    smtp_user = "info@onemultinversiones.com"
    smtp_password = "597925080754084"
    from_email = "info@onemultinversiones.com"
    subject = "ONE multinversiones"

    # Perform replacements
    body = html_body()
    body = body.replace("{{new_message}}", get_message(message))
    body = body.replace("{{company_logo}}", get_logo(logo))
    is_html = True

    # print(to_emails)

    # Create the email message
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = "Undisclosed Recipients"  # Placeholder
    message["Subject"] = subject
    server = None

    if is_html:
        message.attach(MIMEText(body, "html"))
    else:
        message.attach(MIMEText(body, "plain"))

    try:
        if testing:
            print("-------------------------------------")
            print(message)
        else:
            print("************************************")
            # Connect to the SMTP server
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            server.set_debuglevel(1)  # Enable debugging
            server.login(smtp_user, smtp_password)

            # Send email

            # server.sendmail(from_email, to_emails, message.as_string())
            print("Email sent successfully.")
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        server.quit() if server else None


# Example Usage
if __name__ == "__main__":

    import pandas as pd
    import unicodedata
    import time

    def process_csv_and_send_emails(file_path, logo, message):
        def normalize_text(text):
            """
            Normalize text to convert special characters into standard Unicode characters.
            """
            try:
                return (
                    unicodedata.normalize("NFKD", text)
                    .encode("ascii", "ignore")
                    .decode("ascii")
                )
            except Exception as e:
                print(f"Error normalizing text: {text}. Error: {e}")
                return "Unknown Name"

        try:
            # Read the CSV file using pandas
            data = pd.read_csv(
                file_path, delimiter=";", encoding="latin1"
            )  # Adjust encoding as needed

            # Check if required columns are present
            if "nombre" not in data.columns or "email" not in data.columns:
                print(
                    "The CSV file does not contain the required columns: 'nombre' and 'email'."
                )
                return

            # Iterate over the DataFrame rows

            receivers = []
            for _, row in data.iterrows():
                nombre = row["nombre"]
                email = row["email"]

                # Normalize the name to standard Unicode characters
                normalized_nombre = normalize_text(nombre)

                # Split the normalized name into parts
                nombre_parts = normalized_nombre.split()

                receivers.append(email)

                # Print the message
                print(f"Correo enviado a: {nombre} @ {email}")

            #  Send email
            send_email(receivers, "name", logo, message, False)

        except FileNotFoundError:
            print(f"The file at {file_path} was not found.")
        except pd.errors.EmptyDataError:
            print("The CSV file is empty.")
        except Exception as e:
            print(f"An error occurred: {e}")

    # Example usage
    file_path = "data_test.csv"
    process_csv_and_send_emails(file_path, "logo_one", "one_two")
