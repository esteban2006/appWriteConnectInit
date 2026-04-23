import re
import json
import random
import string
import cryptography
import sys
import time
import os
from .cc_execute import *
from .common_functions import *


from pprint import pprint
from datetime import datetime, timedelta, timezone
from appwrite.client import Client
from appwrite.services.databases import Databases  # Import the Databases class
from appwrite.services.account import Account
from appwrite.exception import AppwriteException
from appwrite.id import ID
from appwrite.services.tables_db import TablesDB


# email handling system
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

# jwt token
import jwt
from cryptography.hazmat.primitives import serialization
from jwt import ExpiredSignatureError, InvalidTokenError
from cryptography.hazmat.primitives import serialization

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


app_key = os.getenv("app_key")
client = Client()
client.set_endpoint(os.getenv("appwrite_end_point"))  # Your API Endpoint
client.set_project(os.getenv("project_name"))  # Your project ID
client.set_key(app_key)  # Your secret API key
db_id = os.getenv("db_id")

databases = Databases(client)
tables_db = TablesDB(client)
printer = os.getenv("PRINTER")


def get_millis():
    """
    Get the current time in milliseconds since the Unix epoch.

    Returns:
    - int: Current time in milliseconds.
    """
    return int(time.time() * 1000)


def at_id(email):
    return email.replace("@", "AT")


def remove_at(email):
    return email.replace("AT", "@")


def remove_empty(email):
    return email.replace(" ", "_")


def create_document(collection="xxx", document_id=None, data=None):
    if data is None:
        data = {}

    if printer:

        print(
            f"\n\ncreating document:\n"
            f"collection   : {collection}\n"
            f"document_id  : {document_id}\n"
        )

    if document_id and "@" in document_id:
        document_id = at_id(document_id)

    try:
        # 1️⃣ CHECK IF EXISTS
        try:
            tables_db.get_row(
                database_id=db_id,
                table_id=collection,
                row_id=document_id,
            )

            # EXISTS → UPDATE
            tables_db.update_row(
                database_id=db_id,
                table_id=collection,
                row_id=document_id,
                data=data,
            )

            return {
                "created": False,
                "updated": True,
                "document_id": document_id
            }

        except AppwriteException:
            # DOES NOT EXIST → CREATE
            tables_db.create_row(
                database_id=db_id,
                table_id=collection,
                row_id=document_id,
                data=data,
            )

            return {
                "created": True,
                "updated": False,
                "document_id": document_id
            }

    except AppwriteException as e:
        return e.message


# pprint(create_document(collection="picker_accounts",
#        document_id="test_cc01@gmail.com", data={"millis": str(get_millis())}))


# cc payments -------------------------------------------------
def applicativo_exists(document_id="siaoPages"):
    print(f"Looking for {document_id}")

    try:
        record = common_get_record(
            table_id="data_env",
            row_id=document_id
        )

        if not record:
            print("No record found")
            return False

        print("RECORD:", record)

        # 🔥 ALWAYS decode if string
        wompi = record.get("data")

        if isinstance(wompi, str):
            wompi = common_str_dict(wompi)

        if not wompi:
            wompi = record

        appId = wompi.get("appId")
        appSecret = wompi.get("appSecret")

        if appId and appSecret:
            return [appId, appSecret]

        print("Missing appId or appSecret")
        return False

    except Exception as e:
        print(f"[ERROR] applicativo_exists failed: {str(e)}")
        return False


# pprint(applicativo_exists())


def make_cc_payment(data={}):
    """

    a real declined transaction 

    {'codigoAutorizacion': None,
     'datosAdicionales': {'Apellidos': 'Jandres',
                          'CantidadCompra': '1',
                          'Celular': '70384912',
                          'CodigoPais': 'SV',
                          'CodigoRegion': 'SV-LI',
                          'Direccion': 'Res casa verde 2 calle las rosas 19',
                          'EMail': 'esteban.g.jandres@gmail.com',
                          'EsTrasnaccion3dsTokenizada': 'False',
                          'Nombre': 'Esteban',
                          'NombrePais': 'El Salvador',
                          'NombreRegion': 'La Libertad',
                          'UrlRedirect3dsCliente': 'https://sistemasintegradosao.com/simple-charts.html',
                          'UrlRedirectTransaccion3dsApi': 'https://pagos.wompi.sv/IntentoPago/FinalizarTransaccionApi3ds?id=58a1d0de-bf0b-49f3-abba-1db97effc3de'},
     'datosBitcoin': None,
     'esAprobada': False,
     'esReal': True,
     'fechaTransaccion': None,
     'formaPago': 'PagoNormal',
     'idExterno': None,
     'idTransaccion': '58a1d0de-bf0b-49f3-abba-1db97effc3de',
     'mensaje': None,
     'monto': 250.0,
     'montoOriginal': None,
     'resultadoTransaccion': None}


     """

    applicativo = applicativo_exists(data["applicativo"])

    print(f"ttttttttttttt {applicativo}")

    if not applicativo:
        return {"payment": "failed"}

    this_process = process_cc(
        applicativo[0],
        applicativo[1],
        {
            "name": data["cardholderName"],
            "address": data["address"],
            "year": data["expYear"],
            "cvv": data["securityCode"],
            "month": data["expMonth"],
            "card": data["cardNumber"],
            "email": "esteban.g.jandres@gmail.com",
            "phone": "70384912",
            "amount": data["amount"],
        },
    )

    pprint(this_process)

    if data.get("saveCardData") and this_process.get("urlCompletarPago3Ds"):
        data_to_save = encode(data)

        cd = create_document(
            collection="siao_on_file_cards",
            document_id=remove_empty(data["receiver"]),
            data={"name": data["receiver"], "data": data_to_save},
        )

        if cd == "Document with the requested ID already exists. Try again with a different ID or use ID.unique() to generate a unique ID.":
            cd = create_document(
                collection="siao_on_file_cards",
                document_id=remove_empty(data["receiver"]),
                data={"name": data["receiver"], "data": data_to_save},
            )

    return this_process


print(make_cc_payment(
    data={
        "cardholderName": "Esteban Jandres",
        "cardNumber": "5230450606095469",
        "expMonth": "05",
        "expYear": "2028",
        "securityCode": "741",
        "country": "SV",
        "state": "SV-LI",
        "address": "Res casa verde 2 calle las rosas 19",
        "invoiceId": "TJE6N7",
        "amount": "2.50",
        # "saveCardData": False,
        "receiver": "Tlovendo",
        "applicativo": "wompi_tlovendo",  # siaoPages
    }
))


def check_transaction_status(id="6f490394-5106-4e85-87a8", applicativo="wompi_testin"):

    applicativo = applicativo_exists(applicativo)
    if not applicativo:
        return {"payment": "failed"}

    return get_transacition_status(
        id,
        applicativo[0],
        applicativo[1],
    )


pprint(
    check_transaction_status(
        "d4f1c175-073f-4b63-b3c9-fd2aa65abab2",
        "wompi_tlovendo"
    )
)
