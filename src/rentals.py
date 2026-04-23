import re, json, random, string, cryptography


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
from cryptography.hazmat.primitives import serialization
from jwt import ExpiredSignatureError, InvalidTokenError
from cryptography.hazmat.primitives import serialization


app_key = "standard_c8ed384c3b34a4e773445f193b369cf997fce6a27888f31c6d3fc88fe5f98dce43da0b70024e1a022faab44c0f0ff86e4367e4ced303dca8d00826d9a63379168c95a083bb3028c8da9f48c2192ee08e57356453271b1bf7b413288cba1aa53bf65edd1841326c52777b70db2152b32d113c0cfef76c90ac2c3860cd3c52d963"
client = Client()
client.set_endpoint("https://cloud.appwrite.io/v1")
client.set_project("unit-333")
client.set_key(app_key)
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
###### rentals  ############################################################################################################################
########################################################################################################################################


def encode_data(data_to_encrypt):
    private_key = b"-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQBs3YkuQIbBkk7l82JbmqxV8vb+zEJlS7LyzLhOWrKcgBVelPwt\nkctxxxPbi2JHftSBXJRsJ/zfp+LjixDBNmCIPdBwVQUFFh3YWPB/N6vkHC5sfNX6\nHc3LypVcQavp8UFoCOTj/VPdVW5xqQBul2/vnxxHl8GxiFWn3xsj0eroDPlUb7Zw\nATkHp2+QvjSTZFfy+3IOrPsdqcff5noyIt0axaJ+g4+4OZL1ysU6xAaIk/vsihYa\nCdN3c+ra4XORjwKEC1SiRXueDkkcyQS2XuILBHo2iYaE7QxRQf4JAB0z3DzJtOtj\nygKScrwarXSULrSFGaU6MwxfdMiDDd0FD/HnAgMBAAECggEACGD0ke69cGCGWgRl\naY95/BN7Fxk5cvpkh3NiLAWnAYyKGIF29zrlYZhk2tzbb40/ZcVuVvSs7bnKKKEn\nZPd+bn3zcPHaNQ4CtggCWog6XpAcspTZEysAD9NDs5oKVTMQSaWFmFaDAeH1YiIT\num9FWjfwwUHY0oUfso/lUthxL/LVNEk/AIVvuIhC4jECdsFR+FU04wOQBZRMix1R\nKoHbOnIJDlThmVFxk7LZhxuVHTmcfgSwcIhEQVxjjsyTFGJhuqwkdUo5ZN28/Nbc\ntUAGl9Ple4y8Q7irG5HoTAs2aH1EiAUK9soe7bx1v4xxBTdzxLFlIJcuyqKhPUaI\ni9NH4QKBgQDVWfxdM/d06TTbQPruEO6cRE30jGHX+IQ85fn7HrVySKJk/b2/jRQ0\nSaAFLFwypfA08lUVG58AaOT/NzTguT43nWZ6AylKPjeWajaP3Ap6cffbdYpedkwq\nPM9MyXeVDd2ZYt+8K1bdcQQ+3wEV7P/gZYKt41z9AunbS8dNoRX44wKBgQCCoJgh\nUO0g/8sfdE+GRI0+8rqfzpqQguwvcmtdlmu0f9piOtZ2uyGRkijcYPnIeb8Yz4Ol\n+1YTvE4cz1C3VrgE6Mg48zl+XNZmo8J9+5YwYrflojqmGvcFMGmQQs5ycOxQtbmg\nTrno18TLzIOI/6w9rtuyAsXZrHU15kjnYPCmLQKBgQCaI20EGStKt8GMNiIUJP9+\nvopjh5iY498F8FDucH0+l+Nbe0a/QTm7nQWTNz1VCjXEyt9VZKM3NJFdIZF+Wdbt\nbzY+KFKIZPLcJNhOjvazB+u+Delt3aGhUlWicFuIwH+89YYW+GjFi4U5tvudz5/9\nitkisATadmRmHxVarGqnaQKBgG+GTvw6zImc+j3bnr3Cr1jsAXvI99uje6SyqonX\nkBMmCTxOgaYS9IEFaY9l2DxZ/VZgbUR7xizJW2NreL1e83N1juRYfGCvQHmXHMlU\n0BB1aA5NKIeChB3RDH+XGg1I7emmjVoZfM4X0bQx4qdHqjVrobRke6jxfYzMFLg+\n4pbtAoGBAMyZ30w3CEUMImoMKNhV8g8ZUO4mur4QHpwDsU8bkP/KdkRIkUGXjWJ2\n512oDCUNtwVbib9bUGhqie/0NurQn3eamwgR/sx88n6T6aG+nQfPgDNHAc6N5Mzb\nMTf+j68ImBnljIKtu5gPjE+k2P3PxAlGB19cbynFo3R4MgPw3bFJ\n-----END RSA PRIVATE KEY-----\n"
    return jwt.encode(data_to_encrypt, private_key, algorithm="RS256")


def decode_data(encoded):
    public_key = b"-----BEGIN PUBLIC KEY-----\nMIIBITANBgkqhkiG9w0BAQEFAAOCAQ4AMIIBCQKCAQBs3YkuQIbBkk7l82JbmqxV\n8vb+zEJlS7LyzLhOWrKcgBVelPwtkctxxxPbi2JHftSBXJRsJ/zfp+LjixDBNmCI\nPdBwVQUFFh3YWPB/N6vkHC5sfNX6Hc3LypVcQavp8UFoCOTj/VPdVW5xqQBul2/v\nnxxHl8GxiFWn3xsj0eroDPlUb7ZwATkHp2+QvjSTZFfy+3IOrPsdqcff5noyIt0a\nxaJ+g4+4OZL1ysU6xAaIk/vsihYaCdN3c+ra4XORjwKEC1SiRXueDkkcyQS2XuIL\nBHo2iYaE7QxRQf4JAB0z3DzJtOtjygKScrwarXSULrSFGaU6MwxfdMiDDd0FD/Hn\nAgMBAAE=\n-----END PUBLIC KEY-----\n"
    return jwt.decode(encoded, public_key, algorithms=["RS256"])


def get_collection_id(collection_name):
    collection_ids = {
        "wegsite_data": "675f2e06002cfae516cb",
        "land_lord_account": "675f46ed001227e40b0b",
        "tenant_account": "675f46d1002e8c2f8341",
        "sessions": "6762ea70001495ca22d2",
    }
    return collection_ids.get(collection_name)


def create_rentals_uid(length=32):
    """Generates a valid Appwrite document ID."""
    characters = string.ascii_letters + string.digits + "_"
    return "RENTALS_" + "".join(random.choice(characters) for i in range(length))


def at_id(email):
    return email.replace("@", "AT")


def create_document(collection="xxx", document_id=None, data={}):

    # print("creating rental document")
    # print(f"db_id {db_id} collection {collection} document_id {document_id} ")

    data_data = encode_data(data["data"])

    result = databases.create_document(
        database_id=db_id,
        collection_id=get_collection_id(collection),
        document_id=document_id,
        data={"data": data_data},
    )
    # Remove any keys starting with '$' or if the key is 'all_visits'
    if isinstance(result, dict):
        return {"created": True}

    return result
