import os
import requests
import re
import json
import random
import string
from datetime import datetime
from pprint import pprint
from appwrite.client import Client
from appwrite.services.databases import Databases  # Import the Databases class
from appwrite.services.account import Account
from appwrite.exception import AppwriteException


def test_mam():

    url = "https://66d8eaff7f146a2c2ab3.appwrite.global//v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    data = {
        "update": "mamLogin",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "teamId": 40,
        "next": 5,
    }

    response = requests.post(url, headers=headers, json=data)
    pprint(response.json())


def get_user_api():
    from requests import get

    ip = get("https://api.ipify.org").text
    # print("My public IP address is: {}".format(ip))
    return ip


def get_ip_details():
    # https://freeipapi.com/

    ip_address = "{IP-ADDRESS}"
    url = f"https://freeipapi.com/api/json/{get_user_api()}"

    response = requests.get(url)
    data = response.json()

    pprint(data)


# get_ip_details()


def login():
    url = "https://66d8eaff7f146a2c2ab3.appwrite.global//v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    data = {
        "update": "mamLogin",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "email": "test.jandres@gmail.com",
        "password": "password",
    }

    response = requests.post(url, headers=headers, json=data).json()
    pprint(response)


# login()


def create_account():
    url = "https://66d8eaff7f146a2c2ab3.appwrite.global//v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    user = "creation1"
    email = f"{user}@gmail.com"

    data = {
        "update": "mamCreateAccount",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "email": email,
        "user_name": user,
        "password": user,
        "referred_by": "38B6LE115",
    }

    response = requests.post(url, headers=headers, json=data).json()
    pprint(response)


# create_account()


def get_world_list():

    print("sending get_world_list")

    url = "https://66d8eaff7f146a2c2ab3.appwrite.global//v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    data = {
        "update": "leaguesByCountry",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "public_key": "348EUM2DFNASJ$C$8RZEVHELLZJM1RYX34KU6WYPOJQLSNVAHK5I4B",
    }

    response = requests.post(url, headers=headers, json=data).json()
    pprint(response)


# print(get_world_list())


def update_favs():
    url = "https://66d8eaff7f146a2c2ab3.appwrite.global//v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    data = {
        "update": "addFavs",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "email": "test.jandres@gmail.com",
        "account_id": "3D8Y8SFFN",
        "fav_teams": "[40, 487]",
        "public_key": "348EUM2DFNASJ$C$8RZEVHELLZJM1RYX34KU6WYPOJQLSNVAHK5I4B",
    }

    response = requests.post(url, headers=headers, json=data).json()
    pprint(response)


# update_favs()


def get_next_games():
    url = "https://66d8eaff7f146a2c2ab3.appwrite.global//v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    data = {
        "update": "nextGames",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "teamId": "529",
        "next": "1",
    }

    response = requests.post(url, headers=headers, json=data).json()
    pprint(response)


# get_next_games()


def ccPyament():
    url = "https://66d8eaff7f146a2c2ab3.appwrite.global/v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    data = {
        "update": "process_payment",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "payment_data": {
            "cardholderName": "Esteban Jandres",
            "cardNumber": "5230450606095469",
            "expMonth": "05",
            "expYear": "2028",
            "securityCode": "741",
            "country": "SV",
            "state": "SV-LI",
            "address": "Res casa verde 2 calle las rosas 19",
            "invoiceId": "TJE6N7",
            "amount": "2",
            "saveCardData": False,
            "receiver": "OPORTUNIDAD LTD",
            "applicativo": "wompi_tlovendo",  # siaoPages
        },
    }

    response = requests.post(url, headers=headers, json=data).json()
    print(response)


# ccPyament()


def cc_status():
    url = "https://66d8eaff7f146a2c2ab3.appwrite.global//v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    data = {
        "update": "transaction_status",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "id": "id",
        "applicativo": "wompi_testing",
    }

    response = requests.post(url, headers=headers, json=data).json()
    pprint(response)


# cc_status()


def getTeamName(teamId):
    url = "https://66d8eaff7f146a2c2ab3.appwrite.global//v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    data = {
        "update": "teamName",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "teamId": teamId,
    }

    response = requests.post(url, headers=headers, json=data).json()
    pprint(response)


# getTeamName(39)

API_KEY = "dc2ccb6b5cd7176eafc24cc845c95408"


def get_live_matches(api_key):
    """
    Fetch all currently live football matches using API-Football.
    """
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    # url = "https://v3.football.api-sports.io/fixtures?date=2025-12-02"
    headers = {
        "x-apisports-key": api_key,
    }
    params = {"live": "all"}  # tells API-Football to return all live matches

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()

        # Optional: clean result
        live_matches = data.get("response", [])

        pprint(live_matches)

        return live_matches

    except Exception as e:
        print("Error fetching live matches:", e)
        return []


# live = get_live_matches(API_KEY)


def save_picker_text():
    url = "https://66d8eaff7f146a2c2ab3.appwrite.global/v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    data = {
        "update": "save_piker_text",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "email": "eggsteban@gmail.com",
        "text": "text 02",
        "status": "new",
    }

    r = requests.post(url, headers=headers, json=data)

    print("STATUS:", r.status_code)
    print("HEADERS:", r.headers.get("content-type"))
    print("RAW RESPONSE:")
    print(r.text)

    # Only parse JSON if it actually is JSON
    if r.headers.get("content-type", "").startswith("application/json"):
        pprint(r.json())


# save_picker_text()


def get_piker_account_by_target():
    url = "https://66d8eaff7f146a2c2ab3.appwrite.global/v1/functions/66d8eafc002b0ee3af95/executions"
    headers = {"Content-Type": "application/json"}

    data = {
        "update": "get_piker_account_by_target",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "id": "eggsteban@gmail.com",
        "password": None,
    }

    r = requests.post(url, headers=headers, json=data)

    print("STATUS:", r.status_code)
    print("HEADERS:", r.headers.get("content-type"))
    print("RAW RESPONSE:")
    print(r.text)

    # Only parse JSON if it actually is JSON
    if r.headers.get("content-type", "").startswith("application/json"):
        pprint(r.json())


# get_piker_account_by_target()


def print_tree(start_path=".", prefix=""):
    items = sorted(os.listdir(start_path))

    for i, item in enumerate(items):
        path = os.path.join(start_path, item)
        connector = "└── " if i == len(items) - 1 else "├── "

        print(prefix + connector + item)

        if os.path.isdir(path):
            extension = "    " if i == len(items) - 1 else "│   "
            print_tree(path, prefix + extension)


print(print_tree())


# with open("function/requirements.txt", "w", encoding="utf-8") as f:
#     f.write("""appwrite
# PyJWT
# cryptography
# tronpy
# mnemonic
# segno
# web3
# eth-account
# openai
# """)
