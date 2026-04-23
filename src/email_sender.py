import smtplib
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(to_emails: str, name: str = "name") -> None:
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

    smtp_server = "mail.onemultinversiones.com"
    smtp_port = 465
    smtp_user = "info@onemultinversiones.com"
    smtp_password = "597925080754084"
    from_email = "info@onemultinversiones.com"
    to_emails = [to_emails]
    subject = "Terminando Fase de terracería."
    body = """


<!DOCTYPE html>
<html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Carta Informativa - Proyecto ONE</title>
        <style>
            body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f9f9f9;
            color: #333;
            }
            .container {
            max-width: 800px;
            margin: 30px auto;
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            h1 {
            text-align: center;
            color: #444;
            }
            p {
            margin: 10px 0;
            }
            ul {
            margin: 10px 0 20px 20px;
            list-style-type: disc;
            }
            .signature {
            margin-top: 40px;
            text-align: center;
            }
            .signature-line {
            margin-top: 10px;
            border-top: 1px solid #333;
            width: 300px;
            margin-left: auto;
            margin-right: auto;
            }
            .contact-info {
            margin-top: 30px;
            font-size: 0.9em;
            color: #666;
            }
            .highlight {
            color: #d9534f;
            font-weight: bold;
            }
            a {
            color: #0275d8;
            text-decoration: none;
            }
            a:hover {
            text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <img 
                src="https://onemultinversiones.com/assets/img/LOGOS_/Logo_Fondo%20Blanco.png" 
                alt="Image" 
                style="width: 256px; height: 256px; margin: 20px 0;">
            <h1>Santa Tecla, 13 de Mayo del 2025</h1>
            <p>
                Buen día, estimados clientes de Multi Inversiones One:
            </p>
            <br>
            <p>
                Esperamos que se encuentren bien en sus labores. Por este medio, les solicitamos amablemente que nos confirmen si han recibido sus comprobantes digitales. En caso de no haberlos recibido, les agradecemos comunicarse al número <a href="https://api.whatsapp.com/send?phone=+50360247030&text=Hello%20ONE%20!!!." target="_blank">WhatsApp: 60247030</a>.

            </p>
            
            <br>
           <p>

            Además, hemos notado que algunas transferencias no incluyen el nombre del remitente, lo que nos dificulta su correcta identificación. Por ello, les pedimos encarecidamente que, al momento de realizar el pago, envíen el comprobante correspondiente a nuestro número de WhatsApp. Agradecemos mucho su atención y colaboración.

           </p>
           <br>

           <p>
            Gracias por su atención. 

           </p>

            
            <p>
                Administración Multi Inversiones One.
            </p>
        </div>
        </div>
    </body>
</html>


    """

    body = """


<!DOCTYPE html>
<html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Carta Informativa - Proyecto ONE</title>
        <style>
            body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f9f9f9;
            color: #333;
            }
            .container {
            max-width: 800px;
            margin: 30px auto;
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            h1 {
            text-align: center;
            color: #444;
            }
            p {
            margin: 10px 0;
            }
            ul {
            margin: 10px 0 20px 20px;
            list-style-type: disc;
            }
            .signature {
            margin-top: 40px;
            text-align: center;
            }
            .signature-line {
            margin-top: 10px;
            border-top: 1px solid #333;
            width: 300px;
            margin-left: auto;
            margin-right: auto;
            }
            .contact-info {
            margin-top: 30px;
            font-size: 0.9em;
            color: #666;
            }
            .highlight {
            color: #d9534f;
            font-weight: bold;
            }
            a {
            color: #0275d8;
            text-decoration: none;
            }
            a:hover {
            text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <img 
                src="https://onemultinversiones.com/assets/img/LOGOS_/Logo_Fondo%20Blanco.png" 
                alt="Image" 
                style="width: 256px; height: 256px; margin: 20px 0;">
            <h1>Santa Tecla, 11 de Junio 2025</h1>
            <p>
                Estimados clientes de Proyecto One Tower:

            </p>
            <br>
            <p>
                Reciban un cordial saludo. Nos complace informarles que estamos por concluir la etapa de terracería del proyecto y se tiene previsto iniciar la siguiente fase que son las fundaciones a finales de junio.
                
            </p>
            
            <br>
           <p>

            Asimismo, nos complace comunicarles que el proyecto cuenta con el respaldo financiero de Banco Azul, S.A de C.V, el cual ofrecerá una tasa preferencial exclusiva para los clientes que han depositado su confianza en Torre ONE. Los detalles de esta tasa serán notificados a inicios de julio.

                <br>

            Agradecemos profundamente su confianza y quedamos a su entera disposición para cualquier consulta o comentario.
           </p>
           <br>

           <p>
            Atentamente,


           </p>

            
            <p>
                Multi Inversiones One
            </p>
        </div>
        </div>
    </body>
</html>





    """

    # body = body.replace("{{Propietarios}}", name.upper())
    is_html = True

    # Create the email message
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = ", ".join(to_emails)
    message["Subject"] = subject

    # Attach the body as HTML or plain text
    if is_html:
        # Correctly mark the body as HTML
        message.attach(MIMEText(body, "html"))
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


# Example Usage
if __name__ == "__main__":
    # send_email("esteban.g.jandres@gmail.com", "name")

    import pandas as pd
    import unicodedata
    import time

    def process_csv_and_send_emails(file_path):
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
            for _, row in data.iterrows():
                nombre = row["nombre"]
                email = row["email"].upper()

                # Normalize the name to standard Unicode characters
                normalized_nombre = normalize_text(nombre)

                # Split the normalized name into parts
                nombre_parts = normalized_nombre.split()

                # Determine the greeting format based on the number of parts
                if len(nombre_parts) > 3:
                    name = f"{nombre_parts[0]} {nombre_parts[3]}"
                    greeting = name
                    send_email(email, name)
                elif len(nombre_parts) > 1:
                    name = f"{nombre_parts[0]} {nombre_parts[1]}"
                    greeting = name
                    send_email(email, name)
                elif len(nombre_parts) > 0:
                    greeting = f"{nombre_parts[0]}"
                    send_email(email, f"{nombre_parts[0]}")
                else:
                    greeting = "Unknown Name"

                # Print the message
                print(f"Correo enviado a:  {greeting}! a {email}")
                time.sleep(30)

        except FileNotFoundError:
            print(f"The file at {file_path} was not found.")
        except pd.errors.EmptyDataError:
            print("The CSV file is empty.")
        except Exception as e:
            print(f"An error occurred: {e}")

    # Example usage
    file_path = "data1.csv"  # Replace with your actual CSV file path
    process_csv_and_send_emails(file_path)
