# from encodings.punycode import T
# from turtle import update
# from winreg import OpenKey

import ipaddress
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError
from jwt.exceptions import InvalidKeyError
# from main_helpers import print_centered_banner
import segno
# from tronpy import Tron
# from tronpy.providers import HTTPProvider
# from tronpy.keys import PrivateKey
import base58
import base64
from ast import ClassDef
from datetime import datetime
import re
import json
import random
import string
import sys
import time
import requests
import jwt
import copy
import os
import io
import ast
import hashlib


from pprint import pprint
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from appwrite.services.tables_db import TablesDB
from appwrite.client import Client
from appwrite.services.databases import Databases  # Import the Databases class
from appwrite.services.account import Account
from appwrite.exception import AppwriteException
from appwrite.id import ID
from appwrite.query import Query


import zlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend


# import warnings
# warnings.filterwarnings("ignore",
#                         message="Call to deprecated function 'get_document'",
#                         category=DeprecationWarning)
# warnings.filterwarnings("ignore",
#                         message="Call to deprecated function 'update_document'",
#                         category=DeprecationWarning)

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


# manual process --------------------------------------------------

class Main:

    def __init__(self):

        self.start_timestamp_ = None

        # env vars ----------------
        self.db_id = os.getenv("db_id")
        self.client = Client()
        self.client.set_endpoint(
            os.getenv("appwrite_end_point"))  # Your API Endpoint
        self.client.set_project(os.getenv("project_name"))  # Your project ID
        self.client.set_key(os.getenv("app_key"))  # Your secret API key
        self.databases = Databases(self.client)
        self.tables_db = TablesDB(self.client)

        self.football_api_key = os.getenv("football_api_key")
        self.leages_by_country_collection_id = os.getenv(
            "leages_by_country_collection_id")
        self.leagues_by_country_document_id = os.getenv(
            "leagues_by_country_document_id")
        self.get_teams_in_league_collection_id = os.getenv(
            "get_teams_in_league_collection_id")
        self.next_games_collection_id = os.getenv("next_games_collection_id")
        self.mam_login = os.getenv("mam_login")

        self.season = datetime.now().year - 1
        self.api_url = "https://v3.football.api-sports.io/"
        self.football_api_key = os.getenv("football_api_key")

        self.not_started = ["Time To Be Defined", "Not Started"]
        self.live_by_game_status = [
            "First Half",
            "Kick Off",
            "Halftime",
            "Second Half",
            "2nd Half Started",
            "Extra Time",
            "Break Time",
            "Penalty In Progress",
            "In Progress",
        ]
        self.not_live_by_game_status = [
            "Match Finished",
            "Match Postponed",
            "Match Cancelled",
            "Match Abandoned",
            "Technical Loss",
            "WalkOver",
        ]
        self.start_timestamp = None
        self.add_next_round_games = True if os.getenv(
            "add_next_round_games") else False

        # wallet -------------------------------------------------------

        # self.client = Tron(HTTPProvider(api_key=os.getenv("tron_api_one")))
        # self.client = Tron()
        self.USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
        self.API_URL_BASE = 'https://api.trongrid.io/'
        self.METHOD_BALANCE_OF = 'balanceOf(address)'

        # update controls ------------------------------------------
        self.is_balance_being_updated = False

        self.one_minute = 60
        self.one_hour_control = 3600

        self.ip_encode_key = b"QwErTyUiOpAsDfGhJkLzXcVbNm123456"[
            :32]   # <-- FIXED

    # manual control ---------------------------------------------------------------------------------

    def gen_qr(self, email, id, content, key=None):

        production = os.getenv("production").lower()

        if production == "true":
            account_valid = self.account_valid(email, id, key)

            print(
                f"\n\nPRODUCTION MODE - GEN QR >>> \naccount valid >>> {account_valid} \n\n")

            if account_valid == True:
                return self.get_qr(content)
            else:
                return account_valid

    def account_valid(self, email, id, key=None):

        open_key = None
        valid_account_one = None
        production = os.getenv("production").lower()

        if production == "true":

            print(
                f"PRODUCTION ENV")

            if key is None:
                return False

            try:
                open_key = self.decode_data(key)
                # pprint(open_key)

            except Exception as e:
                return {"error_id": "0x000uab01.1", "message": "invalid key"}

            if open_key is not None:
                valid_account_one = email == open_key["email"] and id == open_key["id"]
                open_key = None

                if not valid_account_one:
                    return {"message": "invalid key contents", "error_id": "0x000uab03"}

        else:
            print(f"NOT PRODUCTION ENV\nemail {email} \nid {id} \nkey {key}")

        cx_account = self.get_document(
            self.mam_login,
            self.at_id(email),
            "account_id_valid CC 01"
        )

        if not cx_account:
            return False

        cx_email = cx_account["email"]
        cx_id = cx_account["account_id"]
        return (cx_email == email and id == cx_id)

    def account_valid_(self, current_ip):

        ip_control_table = "mam_not_logged_in_ip_control"

        ip_record = self.get_document(ip_control_table, current_ip)

        print(ip_record)

        return False

    # wallets internal control ---------------------------------------------------------------------------------

    def create_tron_wallet(self):
        wallet_info = self.client.generate_address_with_mnemonic()
        wallet = wallet_info[0]
        wallet["seed"] = wallet_info[1]
        return wallet

    def get_mam_lightning_status(self, email, id, strike_invoice_id=None, key=None):

        balance = 0

        # if not doc and account is valid create the address
        valid_account = self.account_valid(email, id, key)

        if isinstance(valid_account, (dict)):
            if "message" in valid_account:
                return valid_account

        if strike_invoice_id is None:
            doc = self.get_document("mam_wallets", self.at_id(
                email), "get_infile_strike_id 01")

            if not doc:
                return {"status": "payment id does not exits"}

            else:
                if "lighting" in doc[0]:

                    current_wallet = doc[0]["lighting"]
                    current_wallet = self.decode_data(current_wallet)
                    strike_invoice_id = current_wallet.get("invoiceId", "")

        current_status = self.get_invoice_strike_by_id(strike_invoice_id)
        # pprint(current_status)

        if "state" in current_status:

            if current_status["state"] == "PAID":
                return {
                    "code": 200,
                    "status": "PAID",
                    "Balance": f"{current_status['amount']['amount']} {current_status['amount']['currency']}"
                }
            return {
                "code": 200,
                "status": "UNPAID"
            }
        else:
            return {
                "code": 404,
                "status": "NOT FOUND"
            }

    def get_infile_strike_id(self, email, id, amount=10, deposit_request=False, key=None):

        # if not doc and account is valid create the address
        valid_account = self.account_valid(email, id, key)

        if isinstance(valid_account, (dict)):
            if "message" in valid_account:
                return valid_account

        else:
            print(f"is account valid {valid_account}")

        doc = self.get_document("mam_wallets", self.at_id(
            email), "get_infile_strike_id 01")

        # pprint(doc)

        if not doc:

            print("creating new lightning deposit")
            strike = self.get_lightning_deposit_address(amount, key)
            # pprint(strike)
            current_wallet_data = {}
            current_wallet_data["lighting"] = self.encode_data(strike)
            create = self.create_document(
                "mam_wallets",
                self.at_id(email),
                data={
                    "data": self.make_data_string(current_wallet_data)
                }
            )

            if create["created"]:
                pprint(strike)
                return strike["lnInvoice"]

        else:
            if "lighting" in doc[0]:

                current_wallet = doc[0]["lighting"]
                current_wallet = self.decode_data(current_wallet)

                expiration = current_wallet["expiration"]
                invoice_creation = self.convert_to_milliseconds(expiration)
                invoiced_expired = self.minutes_after_last_update(
                    invoice_creation, self.get_millis(), 1)

                pprint(current_wallet)

                if not invoiced_expired:
                    print(
                        "Lighting invoice still valid --------------------------------------->")

                    # current_wallet = {
                    #     "conversionRate": {
                    #         "amount": "83462.0039",
                    #         "sourceCurrency": "BTC",
                    #         "targetCurrency": "USDT"
                    #     },
                    #     "description": "Mano a mano purchase id eyJEuY1KlC7i11MpL4C01IHctDEAeg",
                    #     "expiration": "2025-03-15T16:52:19.317314+00:00",
                    #     "expirationInSec": 58,
                    #     "invoiceId": "fc3453f5-2681-409c-a2f3-b53ef513008d",
                    #     "lnInvoice": "lnbc4zq24u4elsmavzwdjn9rk0a6djsq5739ww",
                    #     "quoteId": "f655c0fb-113f-40ec-8b24-66dab467007f",
                    #     "sourceAmount": {
                    #         "amount": "0.00023963",
                    #         "currency": "BTC"
                    #     },
                    #     "targetAmount": {
                    #         "amount": "20.00",
                    #         "currency": "USDT"
                    #     }
                    # }

                    return current_wallet["lnInvoice"]

                else:

                    keeper = doc[0]["lighting"]
                    del doc[0]["lighting"]
                    updated_lighting = self.update_document(
                        "mam_wallets",
                        self.at_id(email),
                        {
                            "data": self.make_data_string(doc[0])
                        },
                        "updated_lighting -"
                    )

                    if updated_lighting["created"]:

                        strike_invoice_data = self.get_invoice_strike_by_id(
                            current_wallet["invoiceId"])

                        pprint(strike_invoice_data)

                        balance = 0

                        if strike_invoice_data["state"] == "PAID":
                            balance = float(
                                strike_invoice_data["amount"]["amount"])

                        # else:
                        #     if strike_invoice_data["state"] not in ["PAID", "CANCELLED"]:
                        #         self.cancel_invoices(
                        #             current_wallet["invoiceId"])
                        #     balance = 0

                        balance = 10

                        print(f"\n\nbalance  >>> : {balance}")
                        if balance > 0:
                            print("updating balance ")
                            current_balance = self.get_account_balance(
                                email, id, key, "lighting")

                            pprint(f"current_balance >>> {current_balance}")

                            if isinstance(current_balance, (dict)):
                                if "message" in current_balance:
                                    return current_balance

                            else:
                                pprint(
                                    f"current_balance ->>> {current_balance}")

                        if deposit_request:
                            strike = self.get_lightning_deposit_address(
                                amount, key)
                            # pprint(strike)
                            current_wallet_data = {}
                            current_wallet_data["lighting"] = self.encode_data(
                                strike)
                            create = self.update_document(
                                "mam_wallets",
                                self.at_id(email),
                                data={
                                    "data": self.make_data_string(current_wallet_data)
                                }
                            )

                            if create["created"]:
                                print(f"\n\nData to pass ... 01")
                                return strike

            else:
                current_wallet_data = self.get_dict(doc[0])
                strike = self.get_lightning_deposit_address(amount, key)
                # pprint(strike)
                current_wallet_data["lighting"] = self.encode_data(strike)
                create = self.update_document(
                    "mam_wallets",
                    self.at_id(email),
                    data={
                        "data": self.make_data_string(current_wallet_data)
                    }
                )
                if create["created"]:
                    print(f"\n\nData to pass ... 02")
                    return strike

    def get_infile_tron_address_info(self, data, debug=False):

        email = data["email"]
        id = data["id"]

        def dbg(msg):
            if debug:
                print(f"[DEBUG tron_info] {msg}\n")

        dbg("START")
        dbg(f"email={email}, id={id}")

        doc = self.get_document(
            "mam_wallets",
            self.at_id(email),
            "get_infile_tron_address_info"
        )

        dbg(f"Document fetched → {doc}")

        if not doc:
            dbg("No document found. Checking account validity…")

            valid_account = self.account_valid_(data["ip"])
            dbg(f"Account valid? {valid_account}")

            if valid_account:
                wallet = self.create_tron_wallet()
                dbg(f"New wallet created → {wallet}")

                base58check_address = self.validate_tron_address(
                    wallet["base58check_address"])["result"]
                hex_address = self.validate_tron_address(
                    wallet["hex_address"])["result"]

                dbg(f"Validation → base58={base58check_address}, hex={hex_address}")

                if base58check_address and hex_address:
                    create = self.create_document(
                        "mam_wallets",
                        self.at_id(email),
                        data={"data": self.make_data_string(
                            {"tron_wallet": self.encode_data(wallet)})}
                    )

                    dbg(f"Wallet document created → {create}")

                    if create["created"]:
                        return {
                            "message": "new wallet created",
                            "created": True,
                            "address": wallet["base58check_address"]
                        }

            else:
                dbg(f"Invalid account")

                return False

        else:
            dbg("Document exists. Processing wallet…")

            if "tron_wallet" in doc[0]:
                dbg("Wallet found in document.")

                current_wallet = self.decode_data(doc[0]["tron_wallet"])
                dbg(f"Decoded wallet → {current_wallet}")

                balance = self.get_balance_usdt_free_api(
                    current_wallet["base58check_address"])
                dbg(f"USDT balance → {balance}")

                tron_min_deposit = float(os.getenv("tron_min_deposit"))
                tron_min_received = float(
                    os.getenv("tron_min_balance_received"))

                dbg(
                    f"Config → min_deposit={tron_min_deposit}, min_received={tron_min_received}")

                if balance == 0:
                    dbg("Balance zero → returning address only")
                    return {"address": current_wallet["base58check_address"]}

                elif balance < tron_min_deposit:
                    dbg("Balance < min_deposit")

                    if balance > tron_min_received:
                        dbg("Balance > min_received → storing wallet in 'with_found'")

                        current_wallets = self.get_document(
                            "mam_wallets_with_found",
                            "tron_wallets",
                            "generate_address_with_mnemonic CC 02"
                        )[0]

                        current_wallets.append(
                            self.encode_data(current_wallet))
                        updated = self.update_document(
                            "mam_wallets_with_found",
                            "tron_wallets",
                            {"data": self.make_data_string(current_wallets)}
                        )

                        dbg(f"'with_found' updated → {updated}")

                        if updated["created"]:
                            del doc[0]["tron_wallet"]

                            main_update = self.update_document(
                                "mam_wallets",
                                self.at_id(email),
                                {"data": self.make_data_string(
                                    self.make_data_string(doc[0]))}
                            )

                            dbg(f"Main wallet removed → {main_update}")

                            valid_account = self.account_valid(email, id)
                            dbg(f"Re-validating account → {valid_account}")

                            if valid_account:
                                wallet = self.create_tron_wallet()
                                dbg(f"New wallet created → {wallet}")

                                base58_check = self.validate_tron_address(
                                    wallet["base58check_address"])["result"]
                                hex_check = self.validate_tron_address(
                                    wallet["hex_address"])["result"]

                                dbg(
                                    f"Validation → base58={base58_check}, hex={hex_check}")

                                if base58_check and hex_check:
                                    create = self.update_document(
                                        "mam_wallets",
                                        self.at_id(email),
                                        data={"data": self.make_data_string(
                                            {"tron_wallet": self.encode_data(wallet)})}
                                    )

                                    dbg(f"New wallet saved → {create}")

                                    if create["created"]:
                                        return {
                                            "message": "new wallet created",
                                            "created": True,
                                            "address": wallet["base58check_address"]
                                        }

                            return {
                                "message": "system has remove the address from our records",
                                "created": False,
                                "address": None
                            }

                    else:
                        dbg("Balance < min_received → deleting tron_wallet")
                        del doc[0]["tron_wallet"]

                        updated = self.update_document(
                            "mam_wallets",
                            self.at_id(email),
                            {"data": self.make_data_string(
                                self.make_data_string(doc[0]))}
                        )

                        dbg(f"Wallet removed due to low balance → {updated}")

            else:
                dbg("Document exists but has NO tron_wallet. Creating new one.")

                current_wallet_data = self.get_dict(doc[0])
                valid_account = self.account_valid(email, id)

                dbg(f"Account valid? {valid_account}")

                if valid_account:
                    wallet = self.create_tron_wallet()
                    dbg(f"Created wallet → {wallet}")

                    base58_check = self.validate_tron_address(
                        wallet["base58check_address"])["result"]
                    hex_check = self.validate_tron_address(
                        wallet["hex_address"])["result"]

                    dbg(f"Validation → base58={base58_check}, hex={hex_check}")

                    if base58_check and hex_check:
                        current_wallet_data["tron_wallet"] = self.encode_data(
                            wallet)

                        updated = self.update_document(
                            "mam_wallets",
                            self.at_id(email),
                            data={"data": self.make_data_string(
                                current_wallet_data)}
                        )

                        dbg(f"Wallet inserted in doc → {updated}")

                        if updated["created"]:
                            return wallet["base58check_address"]

    # free tron - ---------------------------------------------------------------------------------

    def get_usdt_transactions(self, address="TJmmqjb1DK9TTZbQXzRQ2AuA94z4gKAPFh"):

        # res = {'data': [{'block_timestamp': 1740577797000,
        #                  'from': 'TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr',
        #                  'to': 'TDWccSenTzjg1PQ7AXCCBBjcLnHb8SwiZW',
        #                  'token_info': {'address': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
        #                                 'decimals': 6,
        #                                 'name': 'Tether USD',
        #                                 'symbol': 'USDT'},
        #                  'transaction_id': '533f04cb018421f14f467d58b0ba94af000872bf5a98e3b9019b2be50314bd2c',
        #                  'type': 'Transfer',
        #                  'value': '9000000'}],
        #        'meta': {'at': 1741412089979, 'page_size': 1},
        #        'success': True}

        url = f"{self.API_URL_BASE}v1/accounts/{address}/transactions/trc20?limit=100&contract_address={self.USDT_CONTRACT}"
        resp = requests.get(url)

        return (resp.json())

    def validate_tron_address(self, address):
        url = f"{self.API_URL_BASE}wallet/validateaddress"

        payload = {
            "address": address,
            "visible": True
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        return (response.json())

    def address_to_parameter(self, addr):
        return "0" * 24 + base58.b58decode_check(addr)[1:].hex()

    def get_balance_usdt_free_api(self, address="ADDRESS"):
        url = self.API_URL_BASE + 'wallet/triggerconstantcontract'
        payload = {
            'owner_address': base58.b58decode_check(address).hex(),
            'contract_address': base58.b58decode_check(self.USDT_CONTRACT).hex(),
            'function_selector': self.METHOD_BALANCE_OF,
            'parameter': self.address_to_parameter(address),
        }
        resp = requests.post(url, json=payload)
        data = resp.json()

        # pprint(data)

        if data['result'].get('result', None):
            print(data['constant_result'])
            val = data['constant_result'][0]
            balance = int(val, 16) / 1000000
            print('balance =', balance)
            return float(balance)
        else:
            print('error:', bytes.fromhex(data['result']['message']).decode())

    # tronpy -------------------------------------------------------------------------------------

    def generate_address_with_mnemonic(self, email, id, ):
        wallet_info = self.client.generate_address_with_mnemonic()
        return {"wallet": wallet_info[0], "seed": wallet_info[1]}

    def get_trx_balance(self, wallet_address):
        try:
            account_info = self.client.get_account(
                wallet_address)

            # Convert to TRX, default to 0
            balance = account_info.get("balance", 0) / 1_000_000
            print(f"Balance of {wallet_address}: {balance} TRX")
            return balance
        except Exception as e:
            print(f"Error fetching balance for {wallet_address}: {e}")

    def get_usdt_balance(self, address):
        try:
            contract = self.client.get_contract(self.USDT_CONTRACT)
            usdt_balance = contract.functions.balanceOf(address)

            balance = usdt_balance / 1_000_000  # Convert from 6 decimals
            print(f"USDT Balance of {address}: {balance} USDT")
            return balance
        except Exception as e:
            print(f"Error fetching USDT balance: {e}")

    def get_account(self, address=""):
        return self.client.get_account(address)

    def get_estimated_energy(self, address, addres_to):

        # Convert the recipient address to its hexadecimal representation
        try:
            # Decode the base58 address to its hexadecimal form
            recipient_hex = to_tvm_address(addres_to).hex()
        except Exception as e:
            raise ValueError(
                f"Invalid recipient address: {addres_to}") from e

        # Pad the recipient address to 32 bytes (64 characters)
        recipient_hex_padded = recipient_hex.rjust(64, "0")

        # Convert the amount to a 32-byte hexadecimal string (64 characters)
        amount_hex = f"{9000000:064x}"

        # Define the function selector and parameter for the USDT transfer
        function_selector = "transfer(address,uint256)"  # USDT transfer
        parameter = recipient_hex_padded + amount_hex  # ABI-encoded parameter

        return self.client.get_estimated_energy(address, self.USDT_CONTRACT, function_selector, parameter)

    def get_network_fee(self, from_address: str, to_address: str, amount: float):
        """
        Estimate the network fee for sending a TRC-20 token (e.g., USDT) on the TRON network.

        :param from_address: The sender's TRON address
        :param to_address: The recipient's TRON address
        :param amount: The amount of the token (USDT) to send
        :return: Estimated network fee (in TRX)
        """
        # Build the transaction
        txn = self.client.trx.transfer(from_address, to_address, amount)

        # Sign the transaction (this does not broadcast it, just prepares it)
        txn = txn.sign()

        # Get the estimated network fee (fee will be in TRX)
        txn_fee = txn.fee  # This will give the fee in TRX

        return txn_fee

    def image_to_base64(self, image_path):
        with open(image_path, "rb") as img_file:
            base64_string = base64.b64encode(img_file.read()).decode("utf-8")
        print(f"data:image/png;base64,{base64_string}")

    def get_qr(self, data):
        # Create QR code with rounded eyes
        # High error correction for logo support
        qr = segno.make_qr(data, error="h")

        # Save QR to a buffer (memory) as PNG
        buffer = io.BytesIO()
        qr.save(buffer, scale=10, dark="#004143",
                light="#ffffff", border=4, kind="png")

        # Convert buffer to Base64 string
        base64_qr = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return f"data:image/png;base64,{base64_qr}"

    def create_gif(self, image1_path, image2_path, output_gif):
        # Open images
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        # Create GIF with 1.5 seconds per frame, loop only once
        img1.save(
            output_gif,
            save_all=True,
            append_images=[img2],
            duration=750,  # 1.5 seconds per frame
            loop=3  # Loop only once
        )

        print(f"GIF saved as {output_gif}")

    def get_qr_two(self, data):
        if data is None:
            data = "TDWccSenTzjg1PQ7AXCCBBjcLnHb8SwiZW"
        usdtTron = "1.1.png"
        save_path = os.path.join(os.getcwd(), "usdtTronQr.png")

        # Generate the QR Code and save it
        version, level, qr_name = myqr.run(
            words=data,
            version=1,
            level="L",
            picture=usdtTron,
            colorized=True,
            contrast=1.0,
            brightness=1.0,
            save_name=save_path
        )
        print(f"{version}\n{level}\n{qr_name}")

        # Convert saved GIF to Base64
        with open(save_path, "rb") as image_file:
            base64_string = base64.b64encode(image_file.read()).decode("utf-8")

        # Optionally, delete the saved file after encoding
        os.remove(save_path)

        return f"data:image/png;base64,{base64_string}"

    def send_usdt(self, private_key: str, from_address: str, recipients: dict):
        """
        Sends different amounts of USDT (TRC-20 token) to multiple recipients in separate transactions.

        :param private_key: Private key of the sender (hex format)
        :param from_address: The sender's TRON address
        :param recipients: A dictionary where keys are recipient addresses and values are amounts to send (in smallest units, e.g., 6 decimal places)
        :param contract_address: The TRC-20 USDT contract address on TRON network
        :return: A dictionary with recipient addresses and their transaction hashes
        """
        client = Tron()  # Initialize TRON client
        pk = PrivateKey(bytes.fromhex(private_key))  # Convert private key

        transaction_results = {}

        for to_address, amount in recipients.items():
            print(f"Sending {amount / 10**6} USDT to {to_address}...")

            # Build, sign, and send the USDT transfer transaction
            txn = (
                client.trx.contract(self.USDT_CONTRACT)
                .functions.Transfer(from_address, to_address, amount * 10**6)
                .with_owner(from_address)
                .build()
                .sign(pk)
                .broadcast()
            )

            # Store transaction hash
            transaction_results[to_address] = txn["txid"]
            print(f"Transaction sent! TXID: {txn['txid']}")

        return transaction_results

    # strike ----------------------------------------------------------------------------------------

    def subscribe_webhook(self, secret="TDWccSenTzjg1PQ7AXCCBBjcLnHb8SwiZW"):

        key = os.getenv("strike_key")

        url = "https://api.strike.me/v1/subscriptions"

        payload = json.dumps({
            "webhookUrl": "https://test1.com/webhook",
            "webhookVersion": "v1",
            "secret": secret,
            "enabled": True,
            "eventTypes": [
                "invoice.updated"
            ]
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {key}'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return (response.json())

    def update_webhook(self, data={}):

        key = os.getenv("strike_key")

        url = "https://api.strike.me/v1/subscriptions/0195543a-64ac-733c-8f17-1e22b0195e0c"

        payload = json.dumps(data)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {key}'
        }

        response = requests.request(
            "PATCH", url, headers=headers, data=payload)

        return (response.json())

    def generate_id(self):
        return f"{''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(40))}"

    def cancel_invoices(self, id):

        url = f"https://api.strike.me/v1/invoices/{id}/cancel"
        key = os.getenv("strike_key")

        payload = {}
        headers = {
            'Accept': 'application/json',
            "Authorization": f"Bearer {key}",
        }

        response = requests.request(
            "PATCH", url, headers=headers, data=payload)

        print(response.text)

    def get_all_invoices(self):

        key = os.getenv("strike_key")
        url = "https://api.strike.me/v1/invoices"

        payload = {}
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {key}",
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        invoices = (response.json())["items"]

        # pprint(invoices)

        for invoice in invoices:
            if invoice["state"] == "UNPAID":
                response = self.cancel_invoices(invoice["invoiceId"])
                # pprint(response.json())
                time.sleep(0.3)

    def get_lightning_deposit_address(self, amount, user_key=None):
        """
        {'conversionRate': {'amount': '66713.3660',
                            'sourceCurrency': 'BTC',
                            'targetCurrency': 'USDT'},
        'description': 'Simple Charts',
        'expiration': '2024-07-29T19:06:36.807+00:00',
        'expirationInSec': 57,
        'lnInvoice': 'lnbc299790n1pn206qzpp5g0rm89dkpn6gqvt5jd8274am52mtq02h72f35el3srn4ltqgsu3qdq42d5k6urvv5syx6rpwf68xcqzzsxqzpesp5pueryyyh5d7et8quqhxwhy7vkn0ml6ua9kq3dhv9hcht2gu63kus9qyyssq5mx4z80xuvj7rhskf04u03vhpg8r3hqndny83cg0w5ju4h578f8j36kv7qgqf607xvwp5qwlvp3e7td4w9xrmfe03257arp2hyqesucp7jq8fx',
        'quoteId': '1682a144-a73d-4687-b226-0ae380312b46',
        'sourceAmount': {'amount': '0.00029979', 'currency': 'BTC'},
        'targetAmount': {'amount': '20.00', 'currency': 'USDT'}}

        """

        key = os.getenv("strike_key")
        user_key = self.encode_internal(
            {"email": self.decode_data(user_key)["email"]})

        data = self.issue_invoice(amount, user_key)

        invoiceId = data["invoiceId"]
        url = f"https://api.strike.me/v1/invoices/{invoiceId}/quote"
        payload = json.dumps({})

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {key}",
        }
        response = requests.request(
            "POST", url, headers=headers, data=payload).json()

        # add invoiceId to the db
        response["invoiceId"] = invoiceId

        return response

    def issue_invoice(self, amount, user_key=None):
        """

        {'amount': {'amount': '20.00', 'currency': 'USDT'},
        'correlationId': '2KGRO41M7K383372CXIG9E3M9ALW58CGF242UREM',
        'created': '2024-07-29T19:23:52.7895579+00:00',
        'description': 'Simple Charts',
        'invoiceId': 'aae7e5ca-7b8d-424a-a86d-579ac44ccedc',
        'issuerId': '6d0ca2af-3009-41ee-80d1-d9566e83d418',
        'receiverId': '6d0ca2af-3009-41ee-80d1-d9566e83d418',
        'state': 'UNPAID'}

        """

        key = os.getenv("strike_key")

        url = "https://api.strike.me/v1/invoices"

        payload = json.dumps(
            {
                "correlationId": f"{self.generate_id()}",
                "description": f"Mano a mano purchase id {user_key}",
                "amount": {
                    "currency": "USDT",
                    "amount": f"{amount}"
                },
            }
        )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {key}",
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        invoice = response.json()
        return invoice

    def get_invoice_strike_by_id(self, id):

        url = f"https://api.strike.me/v1/invoices/{id}"
        key = os.getenv("strike_key")

        payload = {}
        headers = {
            'Accept': 'application/json',
            "Authorization": f"Bearer {key}",
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        return (response.json())

    # btc ----------------------------------------------------------------------------------------

    def createInvoiceD(self,
                       host=None,
                       store_id=None,
                       amount=None,
                       email=None,
                       accountId=None,
                       paymenId=None
                       ):

        headers = {
            'accept': 'application/json',
            'Authorization': 'Basic ZXN0ZWJhbi5nLmphbmRyZXNAZ21haWwuY29tOkJ0b3RvODY4NkA=',
            'Content-Type': 'application/json', }

        data = json.dumps({
            "metadata": {
                "accountId": accountId,
                "email": email,
                "paymenId": paymenId,
            },

            "checkout": {
                "speedPolicy": "HighSpeed",
                "paymentMethods": ["BTC"],
                "defaultPaymentMethod": "BTC",
                "expirationMinutes": 15,
                "monitoringMinutes": 15,
                "paymentTolerance": 99,
                "redirectURL": 'localhost:5000/payed-successfuly',
                "redirectAutomatically": True,
                "requiresRefundEmail": None,
                "checkoutType": None,
                "defaultLanguage": None},
            "receipt": {
                "enabled": True,
                "showQR": True,
                "showPayments": True},
            "amount": amount,
            "currency": "USD",
            "additionalSearchTerms": ["accountId"],
            "availableStatusesForManualMarking": ["None" "PaidLate" "PaidPartial" "Marked" "Invalid" "PaidOver"],
            "status": ["New" "Processing" "Expired" "Invalid" "Settled"]
        })
        response = requests.post(
            f'{host}/api/v1/stores/{store_id}/invoices',
            headers=headers,
            data=data,
        )
        response = response.json()
        # self.sendPaymentEmail(buyerName, buyerEmail,
        #                       response['checkoutLink'], email, lang)
        return response

    def get_btc_invoice_by_id(self, host, storeId,  id="JfsK4ddRUgDmvAHRBvLVGa"):

        url = f"{host}/api/v1/stores/{storeId}/invoices/{id}"
        headers = {
            'accept': 'application/json',
            'Authorization': 'Basic ZXN0ZWJhbi5nLmphbmRyZXNAZ21haWwuY29tOkJ0b3RvODY4NkA=',
            'Content-Type': 'application/json', }
        response = requests.request("GET", url, headers=headers, data={})
        return response.json()

    # ************************************************************************************************

    def get_ip_details(self, user_ip):
        try:
            url = f"https://freeipapi.com/api/json/{user_ip}"
            response = requests.get(url)
            data = response.json()

            print("IP Data:", data)
            print("IP Time Zone:", data.get("timeZone"))

            return data.get("timeZone")

        except Exception as error:
            print("Error fetching IP details:", error)
            return None

    def string_weight_in_megabits(self, text: str, name: str) -> float:
        """
        Calculate the weight of a string in megabits (Mb).

        This function takes a string input, converts it to UTF-8 encoded bytes,
        and then calculates its size in megabits.

        Args:
            text (str): The input string to be measured.

        Returns:
            float: The size of the string in megabits (Mb).
        """
        bytes_size = len(text.encode('utf-8'))  # Get size in bytes
        megabits = (bytes_size * 8) / 1_000_000  # Convert to megabits
        print(
            f"\n\nThe weight of {name} is {(megabits):.6f} Mb.\n\n")

    def get_millis(self):
        """
        Get the current time in milliseconds since the Unix epoch.

        Returns:
        - int: Current time in milliseconds.
        """
        return int(time.time() * 1000)

    def convert_to_human_date(self, timestamp):
        """
        Determine if the timestamp is in seconds or milliseconds and convert to a human-readable date.

        Args:
        - timestamp (int): The timestamp to convert.

        Returns:
        - dict: A dictionary with the conversion results.
        """
        # Check if the timestamp is likely in seconds or milliseconds
        if timestamp > 10**10:  # Likely in milliseconds
            timestamp_type = "milliseconds"
            # Use timezone.utc to handle UTC properly
            human_date = datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        else:  # Likely in seconds
            timestamp_type = "seconds"
            # Use timezone.utc to handle UTC properly
            human_date = datetime.fromtimestamp(
                timestamp, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        return {"timestamp_type": timestamp_type, "human_date": human_date}

    def at_id(self, email):
        return email.replace("@", "AT")

    def remove_at(self, email):
        return email.replace("AT", "@")

    def remove_empty(self, email):
        return email.replace(" ", "_")

    def start_time(self):
        """Record the start time."""
        self.start_timestamp_ = time.time()
        print(
            f"Start time recorded. {self.convert_to_human_date(self.start_timestamp_)}")

    def end_time(self, function=None):
        """Calculate and display the duration since start time."""
        if self.start_timestamp_ is None:
            print("Error: Start time not recorded.")
            return

        end_timestamp = time.time()
        elapsed_time = end_timestamp - self.start_timestamp_
        print(f"{function} Execution time: {elapsed_time:.6f} seconds")

    def determine_winner(self, game):
        teams = game["teams"]
        goals = game["goals"]

        # Check the explicit winner field
        if teams["home"]["winner"] is True:
            print(f"The winner is {teams['home']['name']} (home team)")
            return "home"
        elif teams["away"]["winner"] is True:
            print(f"The winner is {teams['away']['name']} (away team)")
            return "away"

        # Compare goals if winner is not explicitly set
        if goals["home"] > goals["away"]:
            print(f"The winner is {teams['home']['name']} (home team)")
            return "home"
        elif goals["away"] > goals["home"]:
            print(f"The winner is {teams['away']['name']} (away team)")
            return "away"
        else:
            return "draw"

    def convert_to_milliseconds(self, timestamp, by=None):
        """
        Ensure the given timestamp is in milliseconds.
        Supports timestamps in seconds, milliseconds, 'DD-MM-YYYY', and ISO 8601 format.

        Args:
        - timestamp (int, float, or str): The timestamp to check and convert.

        Returns:
        - int: The timestamp in milliseconds.
        """

        if isinstance(timestamp, str):
            # Handle ISO 8601 strings with optional fractional seconds and timezone
            try:
                iso_str = timestamp.replace("Z", "+00:00")

                # If fractional seconds exist, truncate or pad microseconds to 6 digits
                match = re.match(
                    r"(.*T\d{2}:\d{2}:\d{2})(\.\d+)?([+-]\d{2}:\d{2})?$", iso_str)
                if match:
                    time_part = match.group(1)
                    micro_part = match.group(2) or ""
                    tz_part = match.group(3) or ""

                    if micro_part:
                        # Keep only 6 digits
                        micro_part = micro_part[:7].ljust(
                            7, '0')  # includes dot

                    iso_str = f"{time_part}{micro_part}{tz_part}"

                    dt = datetime.fromisoformat(iso_str)
                    return int(dt.timestamp() * 1000)
            except ValueError:
                pass  # Try other formats

            # Try 'DD-MM-YYYY'
            try:
                dt = datetime.strptime(timestamp, "%d-%m-%Y")
                return int(dt.timestamp() * 1000)
            except ValueError:
                pass

            # Try if it's a numeric string
            if timestamp.isdigit():
                timestamp = int(timestamp)
            else:
                raise ValueError(f"Invalid string timestamp: '{timestamp}'")

        # Handle numeric types
        if isinstance(timestamp, (int, float)):
            if timestamp >= 10**12:
                return int(timestamp)  # Already in ms
            elif timestamp < 10**10:
                return int(timestamp * 1000)  # Convert from seconds

        raise ValueError(
            f"Invalid timestamp format: {timestamp}. Must be int, float, or valid date string."
        )

    def minutes_after_last_update(self, first_millis, second_millis, seconds=60):
        """
        Calculate whether a certain number of seconds have passed between two timestamps in milliseconds.

        Args:
            first_millis (int): The earlier timestamp in milliseconds.
            second_millis (int): The later timestamp in milliseconds.
            seconds (int): The threshold in seconds to check if enough time has passed.

        Returns:
            bool: True if the difference between the timestamps exceeds the threshold, False otherwise.
        """

        # Ensure inputs are integers
        first_millis = int(
            self.convert_to_milliseconds(
                first_millis, "minutes_after_last_update 01")
        )
        second_millis = int(
            self.convert_to_milliseconds(
                second_millis, "minutes_after_last_update 02")
        )

        # Calculate the difference in milliseconds
        milliseconds_difference = second_millis - first_millis

        # Convert the difference to seconds
        seconds_passed = milliseconds_difference / 1000

        # Print debug information
        print(f"\nSeconds passed: {seconds_passed:.2f}")

        # Check if the difference exceeds the threshold
        return int(seconds_passed) >= int(seconds)

    def encode_internal(self, data_to_encrypt):

        private_key = os.getenv("secret_jwt")

        if not private_key:
            raise ValueError("Missing PRIVATE_KEY in environment variables")

        # Ensure the input is a dictionary
        if not isinstance(data_to_encrypt, dict):
            raise TypeError("data_to_encrypt must be a dictionary")

        try:
            # Encode JWT with proper error handling
            token = jwt.encode(
                data_to_encrypt, private_key, algorithm="HS256")
            return token

        except InvalidKeyError:
            raise ValueError(
                "Invalid private key. Ensure it is a valid RSA private key.")

        except TypeError as e:
            raise ValueError(f"Invalid data format: {str(e)}")

        except Exception as e:
            raise ValueError(
                f"An unexpected error occurred while encoding JWT: {str(e)}")

    def decode_internal(self, encoded):
        # Check if the encoded token is None or empty
        if not encoded:
            raise ValueError("The JWT token provided is empty or None.")

        public_key = os.getenv("secret_jwt")

        if not public_key:
            raise ValueError("Missing PUBLIC_KEY in environment variables")

        try:
            # Decode JWT with proper error handling
            decoded_payload = jwt.decode(
                encoded, public_key, algorithms=["HS256"])
            return decoded_payload

        except DecodeError:
            raise ValueError(
                "Invalid JWT format. Ensure the token is complete and correctly structured.")

        except ExpiredSignatureError:
            raise ValueError(
                "JWT token has expired. Please obtain a new token.")

        except InvalidTokenError:
            raise ValueError(
                "JWT token is invalid. It may be tampered with or corrupted.")

        except Exception as e:
            raise ValueError(
                f"An unexpected error occurred while decoding JWT: {str(e)}")

    def encode_data(self, data_to_encrypt):

        private_key = os.getenv("private_key")

        if not private_key:
            raise ValueError("Missing PRIVATE_KEY in environment variables")

        # Convert \n to actual newlines
        private_key_bytes = private_key.replace("\\n", "\n").encode()

        # Ensure the input is a dictionary
        if not isinstance(data_to_encrypt, dict):
            raise TypeError("data_to_encrypt must be a dictionary")

        try:
            # Encode JWT with proper error handling
            token = jwt.encode(
                data_to_encrypt, private_key_bytes, algorithm="RS256")
            return token

        except InvalidKeyError:
            raise ValueError(
                "Invalid private key. Ensure it is a valid RSA private key.")

        except TypeError as e:
            raise ValueError(f"Invalid data format: {str(e)}")

        except Exception as e:
            raise ValueError(
                f"An unexpected error occurred while encoding JWT: {str(e)}")

    def decode_data(self, encoded):
        # Check if the encoded token is None or empty
        if not encoded:
            raise ValueError("The JWT token provided is empty or None.")

        public_key = os.getenv("public_key")

        if not public_key:
            raise ValueError("Missing PUBLIC_KEY in environment variables")

        # Convert \n to actual newlines
        public_key_bytes = public_key.replace("\\n", "\n").encode()

        try:
            # Decode JWT with proper error handling
            decoded_payload = jwt.decode(
                encoded, public_key_bytes, algorithms=["RS256"])
            return decoded_payload

        except DecodeError:
            raise ValueError(
                "Invalid JWT format. Ensure the token is complete and correctly structured.")

        except ExpiredSignatureError:
            raise ValueError(
                "JWT token has expired. Please obtain a new token.")

        except InvalidTokenError:
            raise ValueError(
                "JWT token is invalid. It may be tampered with or corrupted.")

        except Exception as e:
            raise ValueError(
                f"An unexpected error occurred while decoding JWT: {str(e)}")

    def get_data_from_dict(self, data={}, path="fixture,status,long"):
        """
        Dynamically retrieves a value from a nested dictionary based on a comma-separated path.

        Args:
            data (dict): The dictionary to retrieve data from.
            path (str): A comma-separated string representing the path to the desired value.

        Returns:
            Any: The value at the specified path, or None if the path is invalid or not found.
        """
        # pprint(data)
        # print(f"path {path}")

        if not data or not path:
            return None

        try:
            keys = path.split(",")  # Split the path into individual keys
            value = data
            for key in keys:
                value = value[key]  # Traverse to the next level
                # print(f"\n\ngetting values : {value}")
            return value
        except (KeyError, TypeError):
            # Handle missing keys or incorrect data types
            return None

    def make_data_string(self, target):
        return json.dumps(target, ensure_ascii=False)

    def make_val_string(self, target):
        return str(target)

    def get_dict(self, target):
        try:
            return json.loads(target)
        except (json.JSONDecodeError, TypeError):
            return target

    def get_today(self):
        return datetime.now().strftime("%d-%m-%Y")

    # appwrite --------------------------------------------------------------------------------

    def get_all_public_saves(self, ip_data=None, login_attempt=False, DEBUG=True):

        # ----------------------------------------------------------
        # Debug helpers
        # ----------------------------------------------------------
        def debug(msg):
            """Print a single debug message"""
            if DEBUG:
                print(msg)

        def debug_block(lines):
            """Print multiple debug lines in a single console output"""
            if DEBUG:
                print("\n".join(lines))

        debug_block([
            "",
            "=== get_all_public_saves_() START ===",
        ])

        current_millis = self.get_millis()
        ip_control_table = "mam_not_logged_in_ip_control"
        calls_in_error = int(os.getenv("calls_in_error"))

        current_ip = (
            ip_data.replace(":", ".") if isinstance(ip_data, str)
            else ip_data.get("ip", "pending").replace(":", ".") if isinstance(ip_data, dict)
            else "pending"
        )

        debug(f"[INFO] Current IP: {current_ip}")

        return_saves = False

        ip_record = self.get_document(ip_control_table, current_ip)

        debug_block([
            "[DEBUG] get_document() returned:",
            f"    {ip_record}"
        ])

        # ----------------------------------------------------------
        # Helper to retry update/create operations
        # ----------------------------------------------------------

        def retry_update_or_create(body, updating=True):
            debug(f"[INFO] retry_update_or_create (updating={updating})")

            for attempt in range(1, 6):
                debug(f"[DEBUG] Attempt {attempt}/5")

                if updating and ip_record:
                    debug("[DEBUG] Updating existing document...")

                    update = self.update_document(
                        ip_control_table,
                        current_ip,
                        {"data": self.encode_data(body)}
                    )

                    debug(f"[DEBUG] update_document() response: {update}")

                    if "created" in update:
                        debug("[SUCCESS] Update succeeded")
                        return True

                else:
                    debug("[DEBUG] Creating new document...")

                    new_doc = self.create_document(
                        ip_control_table,
                        current_ip,
                        {"data": self.make_data_string(body)}
                    )

                    debug(f"[DEBUG] create_document() response: {new_doc}")

                    if "created" in new_doc:
                        debug("[SUCCESS] Create succeeded")
                        return True

            debug("[ERROR] All retry attempts failed")
            return False

        # ==========================================================
        # CASE 1: RECORD EXISTS
        # ==========================================================
        if ip_record:
            debug("[INFO] IP record FOUND. Decoding...")

            data = self.decode_data(ip_record[0])

            debug_block([
                "[DEBUG] Decoded record:",
                f"{data}"
            ])

            gas = data.get("get_all_public_saves")

            # ------------------------------------------------------
            # If GAS missing → Initialize it
            # ------------------------------------------------------
            if not gas:
                debug(
                    "[WARN] get_all_public_saves NOT found. Initializing new entry.")
                base = self.make_ip_base_controller(
                    "get_all_public_saves", current_ip, current_millis, calls_in_error, self.one_hour_control)
                return_saves = retry_update_or_create(base, updating=False)

            else:
                last_update = gas["last_update"]
                error_current, error_limit, wait_window = gas["error_calls"]

                debug_block([
                    f"[INFO] Last update: {last_update}",
                    f"[INFO] Current errors: {error_current}/{error_limit}",
                    f"[INFO] Window: {wait_window} s"
                ])

                can_process = self.minutes_after_last_update(
                    last_update, current_millis, wait_window
                )
                debug(f"[DEBUG] can_process = {can_process}")

                if not can_process:
                    debug("[WARN] Too soon. Increasing error counter.")

                    if error_current > error_limit:
                        debug("[BLOCKED] Too many errors → blocked for 1 hour")
                        return "Your account has been blocked for an hour"

                    gas["error_calls"] = [
                        error_current + 1,
                        calls_in_error,
                        self.one_hour_control
                    ]

                    debug(f"[DEBUG] Updated error_calls: {gas['error_calls']}")

                else:
                    debug("[INFO] Request allowed. Resetting error counter.")

                    gas["error_calls"] = [
                        0, calls_in_error, self.one_hour_control
                    ]

                gas["last_update"] = current_millis
                data["get_all_public_saves"] = gas

                debug_block([
                    "[DEBUG] Data before update:",
                    f"{data}"
                ])

                return_saves = retry_update_or_create(data)

        # ==========================================================
        # CASE 2: RECORD DOES NOT EXIST
        # ==========================================================
        else:
            debug("[INFO] No IP record found → Creating new one")

            base = self.encode_data(
                self.make_ip_base_controller(
                    "get_all_public_saves", current_ip, current_millis, calls_in_error, self.one_hour_control)
            )

            for attempt in range(1, 6):
                debug(f"[DEBUG] Create attempt {attempt}/5")

                new_doc = self.create_document(
                    ip_control_table,
                    current_ip,
                    {"data": self.make_data_string(base)}
                )

                debug(f"[DEBUG] create_document() response: {new_doc}")

                if "created" in new_doc:
                    debug("[SUCCESS] New record created")
                    return_saves = True
                    break

        if login_attempt:
            debug("[INFO] login_attempt=True → Forcing return_saves=True")
            return_saves = True

        debug(f"[INFO] Final return_saves = {return_saves}")
        debug("=== get_all_public_saves_() END ===")

        # ==========================================================
        # PUBLIC SAVES FETCHING
        # ==========================================================
        if return_saves:
            debug("\n=== START FETCHING PUBLIC SAVES ===")

            collection = "mam_public_all"
            documents = []

            limit = int(os.getenv("max_doc_len", "100"))
            offset = 0

            debug_block([
                f"[INFO] limit={limit}",
                f"[INFO] collection={collection}"
            ])

            while True:
                debug(
                    f"\n----- FETCH BATCH (offset={offset}, limit={limit}) -----")

                try:
                    response = self.tables_db.list_rows(self.db_id, collection)

                    rows = response.get("rows", [])
                    debug_block([
                        f"[DEBUG] API response keys: {list(response.keys())}",
                        f"[DEBUG] Received {len(rows)} rows"
                    ])

                    for idx, row in enumerate(rows):
                        debug_block([
                            f"\n[ROW DEBUG] Processing row #{idx+1}",
                            # f"[DEBUG] Raw data: {row.get('data')}"
                        ])

                        try:
                            parsed = self.get_dict(row["data"])
                            documents.append(parsed)

                        except json.JSONDecodeError as e:
                            debug_block([
                                "[ERROR] JSON decode error",
                                f"   Doc ID: {row.get('$id')}",
                                f"   Error : {e}",
                                "   Skipping..."
                            ])

                    if len(rows) < limit:
                        debug("[INFO] Reached final batch.")
                        break

                    offset += limit

                except Exception as e:
                    debug_block([
                        "[ERROR] Exception during list_rows",
                        f"   {e}",
                        "Stopping fetch loop."
                    ])
                    break

            debug_block([
                "=== FETCHING DONE ===",
                f"[INFO] Total documents fetched: {len(documents)}"
            ])

            return documents

    def update_document(self, collection="xxx", document_id=None, data={}, by=None):

        print(
            f"\n\nupdate_document CCC:\n\t"
            f"collection {collection} \n\t"
            f"document_id {document_id} \n\t"
            # f"data {data}\n\t"
            f"{'by' if by is not None else ''} {by if by is not None else ''}\n\n")

        result = None

        try:
            result = self.tables_db.update_row(
                database_id=self.db_id,
                table_id=collection,
                row_id=document_id,
                data=data,
            )

            # Remove any keys starting with '$' or if the key is 'all_visits'
            if isinstance(result, dict):
                return {"created": True}

            return result
        except AppwriteException as e:
            if "Document with the requested ID could not be found" in str(e):
                return {"error": "Document not found"}
            else:
                print(f"error gotten updating doc {e}")
                return result

    def create_document(self, collection="xxx", document_id=None, data={}):
        """
        Create a document in the specified Appwrite collection.

        Parameters:
            collection (str): The collection ID where the document will be created.
            document_id (str or None): The ID of the document. If None, a unique ID will be generated.
            data (dict): The data to store in the document.

        Returns:
            dict: A success message if the document is created.
            bool: False if an exception occurs.
        """
        try:
            # Use ID.unique() if no document_id is provided
            if document_id is None:
                document_id = ID.unique()

            result = self.tables_db.create_row(
                database_id=self.db_id,
                table_id=collection,
                row_id=document_id,
                data=data,
            )

            # Remove any keys starting with '$' or if the key is 'all_visits'
            if isinstance(result, dict):

                return {"created": True, "document_id": document_id}

            else:
                return result

        except AppwriteException as e:

            return e.message

    def get_document(self, collection="xxx", document_id=None, by=None):
        print(f"\nget_document CCC: \n\tcollection {collection} \n\tdocument_id {document_id}")

        try:
            result = self.tables_db.get_row(
                database_id=self.db_id,
                table_id=collection,
                row_id=document_id
            )

            print(f"result at get document {'*'*80}")
            
            # 1. Properly convert the Row object to a dictionary
            # Appwrite objects usually store custom attributes in a dict called 'data' or 'attributes'
            if hasattr(result, 'attributes'):
                res_dict = result.attributes
            elif hasattr(result, 'data'):
                res_dict = result.data
            elif isinstance(result, dict):
                res_dict = result
            else:
                # Fallback for some SDK versions
                res_dict = vars(result)

            # 2. Extract the content from the 'data' column
            data_content = res_dict.get("data")

            if data_content:
                try:
                    parsed_data = self.get_dict(data_content)
                except Exception as e:
                    print(f"JSON Parse error: {e}")
                    parsed_data = {}

                # Return the list format your calling code expects
                return [
                    parsed_data,                         # 0: data
                    res_dict.get("today", "X"),          # 1
                    res_dict.get("counter", "X"),        # 2
                    res_dict.get("last_update", "X"),    # 3
                    res_dict.get("ids", "X"),            # 4
                    res_dict.get("indexes", "X"),        # 5
                    res_dict.get("last_update_date", "X"), # 6
                    res_dict.get("bolts", "X"),          # 7
                    res_dict.get("history", "X"),        # 8
                ]
            else:
                print("WARNING: 'data' column was empty or not found in the record attributes.")
                # Return a list of empty values to prevent KeyError: 0 in calling code
                return [{}, "X", "X", "X", "X", "X", "X", "X", "X"]

        except AppwriteException as e:
            print(f"Appwrite Error: {str(e)}")
            return False
    
    def delete_document(self, collection="xxx", document_id=None):

        try:
            self.tables_db.delete_row(
                database_id=self.db_id,
                table_id=collection,
                row_id=document_id
            )
            return True
        except AppwriteException as e:
            if "Document with the requested ID could not be found" in str(e):
                return "no found"

    def mam_counter_update_(self, external=False):
        try:
            doc_id = "67698638001238f51641"
            data_key = "6769881b003c46ff1595"

            # Fetch doc
            raw = self.get_document(doc_id, data_key, "mam_counter_update ")

            # Document sometimes returns a LIST — take the first valid entry
            cc = raw[0] if isinstance(raw, list) else raw

            today = self.get_today()

            # Ensure data key exists
            # if the document keeps counter inside "data", unwrap it
            if "data" in cc and isinstance(cc["data"], dict):
                cc = cc["data"]

            # Create today's entry if needed
            if today not in cc:
                cc[today] = {"fromApi": 0, "fromLocal": 0}

            # Increment counters
            if external:
                cc[today]["fromApi"] += 1
            else:
                cc[today]["fromLocal"] += 1

            # Save back
            print(self.update_document(
                doc_id,
                data_key,
                {"data": json.dumps(cc)},
                "mam_counter_update "
            ))

        except Exception as e:
            print(
                f"{'*'*80}\n\nError on line: {sys.exc_info()[-1].tb_lineno}\n"
                f"{type(e).__name__}: {e}"
            )

    def mam_counter_update(self, external=False):
        try:
            doc_id = "67698638001238f51641"
            data_key = "6769881b003c46ff1595"
            today = self.get_today()

            raw = self.get_document(doc_id, str(today), "mam_counter_update")

            # print(f"Row or current state ... {raw}")

            if not raw or ("ID could not be found" in raw):
                # print("Create Row")

                self.tables_db.create_row(
                    database_id=self.db_id,
                    table_id=doc_id,
                    row_id=str(today),
                    data={
                        "data": self.make_data_string({"fromApi": 1, "fromLocal": 0})
                    }
                )

            else:
                # print("update row")
                current_data = raw[0]
                current_data["fromLocal"] += 1
                self.update_document(doc_id, str(today), {
                    "data": self.make_data_string(current_data)})

        except Exception as e:
            print(
                f"{'*'*80}\n\nError on line: {sys.exc_info()[-1].tb_lineno}\n"
                f"{type(e).__name__}: {e}"
            )

    # ----- manual process

    def get_escrow_history(self, email="test01.jandres@gmail.com", account_id=None, is_testing=False):
        """
        Retrieve the escrow history for a user.

        This function fetches the escrow history either based on the email (for testing purposes)
        or the account ID (for production use).

        Parameters:
        email (str): The email address of the user. Default is "test01.jandres@gmail.com".
                    This is used only when is_testing is True.
        account_id (str): The account ID of the user. This is used when is_testing is False.
                        If None and is_testing is False, the function returns an error.
        is_testing (bool): A flag to determine whether the function is being used in a testing
                        environment (True) or production environment (False). Default is False.

        Returns:
        dict or bool: If successful, returns the escrow history as a dictionary.
                    If no history is found or an error occurs, returns False.
                    If account_id is None and is_testing is False, returns a dict with an error message.
        """
        print(f"---> Start of get_escrow_history {account_id}")

        if is_testing:

            print(f"get_escrow_history: {email} ")
            result = self.get_document("mam_history", at_id(
                email), "get_escrow_history 01")
            print(
                f"--- > End of get_escrow_history {account_id}", "get_escrow_history 02")

            if result:
                return result[0]
            else:
                return False
        else:
            if account_id is None:
                print(
                    f"--- > End of get_escrow_history {account_id}", "get_escrow_history 03")
                return {"account": "not valid"}

            else:
                print(
                    f"--- > End of get_escrow_history {account_id}", "get_escrow_history 04")

                history = self.get_document(
                    "mam_history", at_id(email), "get_escrow_history 01")

                if history:
                    return history[0]

                else:
                    return []

    def update_account_balance(self, email, id, update, key, by):

        is_valid = self.account_valid(email, id, key)

        # pprint(f"is valid -> {is_valid}")

        if is_valid == True:

            retries = 3  # Number of retries in case of conflicts
            for _ in range(retries):
                try:
                    updated = self.update_document(
                        "mam_balances",
                        self.at_id(email),
                        {'balance': float(update)},
                        f"update_account_balance to --> {update} by {by}"
                    )

                    if "created" in updated:
                        return updated

                    elif updated["error"] == "Document not found":
                        create = self.create_document(
                            "mam_balances",
                            self.at_id(email),
                            {'balance': float(update)}
                        )

                        if "created" in create:
                            return {"create": create["created"]}

                    break

                except Exception as e:
                    print(f"Update failed: {e}. Retrying...")
                    time.sleep(1)  # Wait before retrying
        else:
            return is_valid

    def get_account_balance(self, email, id, key, by):

        if by not in ["login", "lighting", "tron", "bnb"]:
            return {"message": "Not a  valid request"}

        is_valid = self.account_valid(email, id, key)

        # pprint(f"is valid -> {is_valid}")

        if is_valid == True:
            return float(self.get_document("mam_balances", self.at_id(email))["balance"])

        else:
            return is_valid
    # apiFootball ------------------------------------------------------------------------------------------------

    def get_standings(self, league=39):

        retries = 3  # Number of retries in case of conflicts
        for _ in range(retries):
            url = f"{self.api_url}standings?league={league}&season={self.season}"
            headers = {"x-apisports-key": self.football_api_key}

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                return data
            else:
                time.sleep(1)

        return {"error": "Failed to fetch standings", "status_code": response.status_code}

    def get_next_round(self, league_id=2, teams_len=20):

        print(f"getting next round games for {league_id} and len {teams_len}")
        if "NR" in str(league_id):
            league_id = re.sub(r"\D", "", league_id)

        print(
            f"getting next round games for second time {league_id} and len {teams_len}")

        url = f"{self.api_url}fixtures?league={league_id}&next={teams_len + (teams_len // 2)}"
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": self.football_api_key,
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(
                f"Error: Unable to fetch leagues. Status code: {response.status_code}")
            print(f"Response: {response.text}")

            # If we've reached this point, return the default dict
            return {
                "future": {
                    "get": "fixtures",
                    "parameters": {
                        "team": f"NR{league_id}",
                        "next": 1
                    },
                    "errors": [],
                    "results": 1,
                    "paging": {
                        "current": 1,
                        "total": 1
                    },
                    "response": []
                },
                "past": {
                    "get": "fixtures",
                    "parameters": {
                        "team": f"NR{league_id}",
                        "next": 1
                    },
                    "errors": [],
                    "results": 0,
                    "paging": {
                        "current": 1,
                        "total": 1
                    },
                    "response": []
                }
            }

        data = response.json()

        if not data.get("response"):
            print("No data found for the specified league and season.")
            # Iterate over decreasing team lengths
            for new_teams_len in [32, 16, 8, 4, 2, 1]:
                if new_teams_len < teams_len:
                    return get_next_round(league_id, new_teams_len)

        mid_point = len(data["response"]) // 2

        return {
            "future": {
                "get": "fixtures",
                "parameters": {
                    "team": f"NR{league_id}",
                    "next": f"{mid_point}"
                },
                "errors": [],
                "results": mid_point*2,
                "paging": {
                    "current": 1,
                    "total": 1
                },
                "response": data["response"]
            },
            "past": {
                "get": "fixtures",
                "parameters": {
                    "team": f"NR{league_id}",
                    "next": f"{mid_point}"
                },
                "errors": [],
                "results": 0,
                "paging": {
                    "current": 1,
                    "total": 1
                },
                "response": []
            }
        }

    def get_leagues_by_country(self):
        """
        Fetches and organizes football leagues by country from the API.

        - Retrieves league data from the API with up to 5 retries in case of failures.
        - Groups leagues by country and includes league/country images.
        - Sorts leagues, prioritizing "important" leagues from a predefined list.
        - Adjusts specific league names and images for display purposes.
        - Moves the first league entry to the third position in the final list.

        Returns:
            list: A sorted list of leagues grouped by country, or None if data retrieval fails.
        """
        url = f"{self.api_url}leagues"
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": self.football_api_key,
        }

        # Fetch API data with retries
        for attempt in range(5):
            try:
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if "response" in data:
                        break  # Valid response received
                print(f"Attempt {attempt + 1}: Unexpected response format.")
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1}: Request failed - {e}")
            time.sleep(1)
        else:
            print("Error: Failed to fetch valid response after 5 attempts.")
            return None

        main_leagues = self.get_document("data_env", "important_leagues")[0]
        leagues_by_country = defaultdict(list)

        # Aggregate leagues by country
        for league_data in data["response"]:
            country_name = league_data["country"]["name"]
            league_info = {
                "id": league_data["league"]["id"],
                "name": league_data["league"]["name"],
                "league_img": league_data["league"]["logo"],
                "contry_img": league_data["country"].get("flag") or "https://sistemasintegradosao.com/assets/img/siaoLogos/logoX512.png",
            }
            leagues_by_country[country_name].append(league_info)

        # Prepare data for sorting
        sorted_data = []
        for country, leagues in leagues_by_country.items():
            country_data = [country] + leagues
            sorted_data.append(country_data)

        # Custom sort: main leagues first
        def custom_sort_key(item):
            country_name = item[0]
            if country_name in main_leagues:
                return (0, main_leagues.index(country_name))
            return (1, country_name)

        sorted_data.sort(key=custom_sort_key)

        # Update specific leagues
        world_leagues = leagues_by_country.get("World", [])
        fifa_holder = ["Fifa"]
        for league in world_leagues:

            if league["name"] in ["Friendlies", ]:
                league.update(
                    {"name": "FIFA", "contry_img": league["league_img"]})
                sorted_data.insert(0, ["National Teams", league])

            elif league["name"] == "UEFA Europa League":
                league.update({"contry_img": league["league_img"]})
                sorted_data.insert(0, ["Europa League", league])

            elif league["name"] == "UEFA Champions League":
                league.update({"contry_img": league["league_img"]})
                sorted_data.insert(0, ["Champions League", league])

            elif league["name"] == "Clubs":
                league.update({"contry_img": league["league_img"]})
                sorted_data.insert(0, ["ALL Clubs", league])

        # # Reorder the list
        # if sorted_data:
        #     sorted_data.insert(2, sorted_data.pop(1))

        return sorted_data

    def get_teams_of_league(self, league_id, season):
        """
        Fetches and returns the entire API response for teams of a specific league and season,
        with the 'response' field sorted by team name.

        Args:
            league_id (int): ID of the league.
            season (int): The season year (e.g., 2024).
            football_api_key (str): API key for authentication.

        Returns:
            dict: The original API response with the 'response' field sorted by team name.
        """
        url = f"{self.api_url}teams"
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": self.football_api_key,
        }
        params = {
            "league": league_id,
            "season": self.season,
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if "response" in data:
                # Sort the 'response' field by team name
                data["response"] = sorted(
                    data["response"], key=lambda x: x["team"]["name"])

                if self.add_next_round_games:

                    # Create a new entry instead of modifying the existing one
                    sample = copy.deepcopy(
                        data["response"][0]
                    )  # Deep copy to avoid modification issues
                    sample["team"]["code"] = "NR"
                    sample["team"]["name"] = "Next Round Games"
                    sample["team"]["id"] = encode_data(
                        {"league_id": f"NR{league_id}",
                         "teams_len": len(data["response"]) / 2}
                    )
                    sample["team"][
                        "logo"
                    ] = "https://sistemasintegradosao.com/assets/img/siaoLogos/logoX512.png"

                    # Insert the modified copy at the beginning
                    data["response"].insert(0, sample)

                return data
            else:
                print("No team data found in the response.")
                return {}
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return {}

    def get_next_games(self, team_id=50, next_len=3):
        """
        Fetches the past and future games of a given team and reorders the 'response'
        field to prioritize fixtures with 'status.long' in the 'live_by_game_status' list.

        Args:
            team_id (int): ID of the team.
            next_len (int): Number of past and future games to fetch.

        Returns:
            dict: A dictionary containing the reordered 'past' and 'future' fixtures.
        """

        print(f"\n\nget_next_games {team_id}")

        if len(str(team_id)) > 10:  # if id > 10 this meand i am decodeing a jwt
            data = self.decode_data(team_id)
            league_id = data["league_id"]
            teams_len = int(data["teams_len"])
            return self.get_next_round(league_id, teams_len)

        # API details
        url = f"{self.api_url}fixtures"
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": self.football_api_key,
        }

        # Parameters for past and future fixtures
        params_past = {"team": team_id, "last": next_len}
        params_future = {"team": team_id, "next": next_len}

        # Retry logic for past fixtures
        response_past = None
        for attempt in range(5):
            response_past = requests.get(
                url, headers=headers, params=params_past).json()
            if "response" in response_past:
                break
            print(
                f"get_next_games Attempt {attempt + 1} (past fixtures): Retrying in 1 second..."
            )
            time.sleep(1)
        if "response" not in response_past:
            return {"error": "Failed to fetch past fixtures after 5 attempts."}

        # Retry logic for future fixtures
        response_future = None
        for attempt in range(5):
            response_future = requests.get(
                url, headers=headers, params=params_future
            ).json()
            if "response" in response_future:
                break
            print(
                f"Attempt {attempt + 1} (future fixtures): Retrying in 1 second...")
            time.sleep(1)
        if "response" not in response_future:
            return {"error": "Failed to fetch future fixtures after 5 attempts."}

        # Define live game statuses
        # live_by_game_status = [
        #     "First Half",
        #     "Kick Off",
        #     "Halftime",
        #     "Second Half",
        #     "2nd Half Started",
        #     "Extra Time",
        #     "Break Time",
        #     "Penalty In Progress",
        #     "In Progress",
        # ]

        def reorder_fixtures(fixture_list):
            """Reorder fixtures to move live games to the beginning."""
            live_fixtures = [
                f
                for f in fixture_list
                if f["fixture"]["status"]["long"] in self.live_by_game_status
            ]
            other_fixtures = [
                f
                for f in fixture_list
                if f["fixture"]["status"]["long"] not in self.live_by_game_status
            ]
            return live_fixtures + other_fixtures

        # Reorder the response field if it exists
        if "response" in response_past:
            response_past["response"] = reorder_fixtures(
                response_past["response"])
        if "response" in response_future:
            response_future["response"] = reorder_fixtures(
                response_future["response"])

        # Check if the first fixture in response_past is live
        if (
            "response" in response_past
            and response_past["response"]
            and response_past["response"][0]["fixture"]["status"]["long"]
            in self.live_by_game_status
        ):
            # Remove the live fixture from past
            live_fixture = response_past["response"].pop(0)
            # Add the live fixture to the start of future
            if "response" in response_future:
                response_future["response"].insert(0, live_fixture)
            else:
                response_future["response"] = [live_fixture]

        return {
            "past": response_past,
            "future": response_future,
        }

    def fetch_games(self, for_date, liveRequest=False, printRecords=False):
        """
        Fetches football games for a given date and updates the document database if needed.

        Args:
            for_date (str): The date for which games should be fetched (YYYY-MM-DD format).
            liveRequest (bool, optional): If True, forces a fresh API request. Defaults to False.
            printRecords (bool, optional): If True, prints fetched records. Defaults to False.

        Returns:
            list: A list of games for the given date.
        """
        print(f"\n\n***************** > updating games for {for_date}\n\n")

        current_data = self.get_document(
            "mam_today_games_results", "today_results")

        for i in range(len(current_data)):
            print(f"update id {i} {current_data[i]}")
        last_update = current_data[6]
        current_games = current_data[0]  # Stored list of games
        current_millis = self.get_millis()

        print(
            f"Update should occur after 600 seconds\n"
            f"for date {for_date}\n"
            f"last_update : {last_update}\n"
            f"current_millis : {current_millis}"
        )

        if self.minutes_after_last_update(last_update, current_millis, 1) or liveRequest:
            url = f"{self.api_url}fixtures"
            headers = {
                "x-rapidapi-host": "v3.football.api-sports.io",
                "x-rapidapi-key": self.football_api_key,
            }
            params = {"date": for_date}

            response = None
            retries = 5
            while retries > 0:
                try:
                    response = requests.get(
                        url, headers=headers, params=params).json()
                    if "response" in response:
                        break
                except Exception as e:
                    print(f"Error: {e}")
                retries -= 1
                print(f"Retrying... ({5 - retries}/5)")
                time.sleep(1)

            if not response or "response" not in response:
                print(
                    f"Error: Unable to fetch games for {for_date} after multiple attempts.")
                return []

            game_data = response["response"]
            indexes = {str(game["fixture"]["id"]): idx for idx,
                       game in enumerate(game_data)}
            game_ids = list(indexes.keys())

            if printRecords:
                for idx, game in enumerate(game_data):
                    print(f"Game ID {idx}:{game}\n")

            return game_data

        print(f"No update required for {for_date}")
        return current_games

    def today_games(self, liveRequest=False, printRecords=False):
        """
        Fetches today's and yesterday's games and merges them into a single result.

        Args:
            liveRequest (bool, optional): If True, forces fresh API requests. Defaults to False.
            printRecords (bool, optional): If True, prints fetched records. Defaults to False.

        Returns:
            list: A merged list of today's and yesterday's games.
        """
        today = datetime.today().strftime("%Y-%m-%d")
        yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

        today_games = self.fetch_games(today, liveRequest, printRecords)
        yesterday_games = self.fetch_games(
            yesterday, liveRequest, printRecords)

        merged_games = today_games + yesterday_games

        indexes = {str(game["fixture"]["id"]): idx for idx,
                   game in enumerate(merged_games)}
        game_ids = list(indexes.keys())

        self.update_document(
            "mam_today_games_results", "today_results",
            data={
                "data": self.make_data_string(merged_games),
                "last_update": str(self.get_today()),
                "ids": self.make_data_string(game_ids),
                "indexes": self.make_data_string(indexes),
                "last_update_date": self.make_data_string(self.get_millis())
            },
        )

        print(f"Total games fetched and saved: {len(merged_games)}")
        return merged_games

    def get_fixture_by_id(self, fixture_id):
        """
        Fetches fixture data by ID with retry logic to handle missing or failed responses.

        Args:
            fixture_id (int): ID of the fixture to fetch.

        Returns:
            dict: A dictionary containing the fixture data or an error message.
        """
        # Query parameter for the fixture ID
        params = {"id": fixture_id}

        # Headers for authentication
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": self.football_api_key,
        }

        # Retry logic for the API request
        response_data = None
        for attempt in range(5):
            response = requests.get(
                f"{self.api_url}fixtures", headers=headers, params=params
            )
            if response.status_code == 200:
                response_data = response.json()
                if "response" in response_data:
                    break  # Exit the retry loop if "response" is present
            print(f"Attempt {attempt + 1}: Retrying in 1 second...")
            time.sleep(1)

        # Check if the response contains the expected data
        if not response_data or "response" not in response_data:
            print("Failed to fetch fixture data after 5 attempts.")
            return {"error": "Failed to fetch fixture data."}

        # Extract the required fields from the response
        new_data = {}
        for item in response_data["response"]:
            if item.get("teams"):
                new_data["teams"] = item.get("teams", "No 'teams' key found")

            if item.get("goals"):
                new_data["goals"] = item.get("goals", "No 'goals' key found")

            if item.get("fixture"):
                new_data["fixture"] = item.get(
                    "fixture", "No 'fixture' key found")

            # Break after processing the first item to match original logic
            return new_data

        print("No valid data found in the response.")
        return False

    def get_team_name_by_id(self, team_id):
        """
        Fetch the team name by its ID using the Football API.

        Parameters:
            team_id (int): The ID of the team to fetch.

        Returns:
            str: The name of the team if found, otherwise an error message.
        """
        url = f"{self.api_url}teams?id={team_id}"
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": self.football_api_key,
        }

        for attempt in range(5):  # Retry up to 5 times
            response = requests.get(url, headers=headers)

            # Check for response status
            if response.status_code != 200:
                print(
                    f"Error: Unable to fetch team. Status code: {response.status_code}.")
                print(f"Response: {response.text}")
                break

            data = response.json()

            # Check if the API returned the expected data
            if "response" in data and data["response"]:
                # Successfully retrieved the data
                return data

            print(
                f"Attempt {attempt + 1}: Unexpected API response or team not found. Retrying..."
            )
            time.sleep(1)  # Wait 1 second before the next attempt

        return "Error: Failed to fetch team name after 5 attempts."

    def get_lbc(self, data={}, testing=False):

        ip_counter = self.check_ip_exists(data)

        print(f"ip counter at get_lbc")
        # return (ip_counter)

        ip_counter["blocked"] = False
        if not ip_counter["blocked"]:

            try:
                collection_ = self.get_document(
                    self.leages_by_country_collection_id,
                    self.leagues_by_country_document_id,
                )

                # print(collection_)

                collection = {
                    "data": collection_[0],
                    "today": collection_[1],
                    "counter": collection_[2]
                }

                is_today = get_today()
                has_required_fields = "today" in collection and "data" in collection

                if not has_required_fields:
                    print("Missing required fields ('today', 'data') in collection.")
                    return None

                # Check if the stored 'today' matches the current day
                is_today_data = (is_today == collection["today"])

                # Shared counter update
                new_counter = int(collection.get("counter", 0)) + 1

                if is_today_data:
                    # DATA IS UP TO DATE
                    print(
                        f"Updating today: today_match={is_today_data}\n"
                        f"Current Day: {is_today} | Stored Day: {collection['today']}"
                    )

                    self.update_document(
                        collection=self.leages_by_country_collection_id,
                        document_id=self.leagues_by_country_document_id,
                        data={"counter": new_counter},
                    )

                    print(f"Returning cached data")
                    return self.get_dict(collection["data"])

                else:
                    # DATA IS NOT FROM TODAY — refresh needed
                    print(f"Updating NOT today: today_match={is_today_data}")

                    # Testing mode uses local data
                    if testing:
                        import dataAllLeagues
                        leagues_by_country = dataAllLeagues.contry_list
                    else:
                        leagues_by_country = self.get_leagues_by_country()

                    # Update with new data
                    self.update_document(
                        collection=self.leages_by_country_collection_id,
                        document_id=self.leagues_by_country_document_id,
                        data={
                            "data": self.make_data_string(leagues_by_country),
                            "today": is_today,
                            "counter": new_counter,
                        },
                    )

                    return leagues_by_country

            except Exception as e:
                print(
                    f"{'*'*80}\n\nError on line: {sys.exc_info()[-1].tb_lineno}\n"
                    f"{type(e).__name__}: {e}"
                )

        else:
            return ip_counter

    def get_tol(self, league_id=40):
        league_internal_id = f"mam_league_{league_id}"

        # Fetch team doc
        team = self.get_document(
            self.get_teams_in_league_collection_id,
            league_internal_id
        )

        today = self.get_today()

        print(f"league_internal_id: {league_internal_id}\ntoday: {today}")

        try:
            # If no data or outdated
            if not team or today != team[1]:
                tol = self.get_teams_of_league(league_id, self.season)

                # Build team_ids string
                team_ids = [str(item["team"]["id"])
                            for item in tol["response"]]
                tol["team_ids"] = "-".join(team_ids)

                # Try creating the document
                try:
                    create_result = self.create_document(
                        collection=self.get_teams_in_league_collection_id,
                        document_id=league_internal_id,
                        data={
                            "data": self.make_data_string(tol),
                            "today": today,
                            "counter": 1
                        },
                    )

                    # If create returned an error message
                    if create_result == (
                        "Document with the requested ID already exists. "
                        "Try again with a different ID or use ID.unique() "
                        "to generate a unique ID."
                    ):
                        print("update on error")
                        self.update_document(
                            collection=self.get_teams_in_league_collection_id,
                            document_id=league_internal_id,
                            data={
                                "data": self.make_data_string(tol),
                                "today": today,
                                "counter": team[2] + 1,
                            },
                        )

                except AppwriteException as e:
                    print("00")
                    if e.code == 409:  # Conflict
                        print("01")
                        self.update_document(
                            collection=self.get_teams_in_league_collection_id,
                            document_id=league_internal_id,
                            data={
                                "data": self.make_data_string(tol),
                                "today": today,
                                "counter": team[2] + 1,
                            },
                        )
                    else:
                        raise

                # Update counter system
                self.mam_counter_update(True)

                return tol

            else:
                # Cached, valid today
                print("03")

                data = team[0]

                # Show team IDs
                team_ids = [item["team"]["id"] for item in data["response"]]
                print(f"\nteams in league {team_ids}\n")

                # Update counter
                self.update_document(
                    collection=self.get_teams_in_league_collection_id,
                    document_id=league_internal_id,
                    data={"counter": team[2] + 1},
                )

                self.mam_counter_update()

                # Load flags
                current_flags = self.get_document(
                    "mam_teams_flags",
                    "flags",
                    "mam_teams_flags 01"
                )[0]

                # Process new items
                processed_data = {
                    item["team"]["name"].lower(): {"logo": item["team"]["logo"]}
                    for item in data["response"]
                    if len(str(item["team"]["id"])) < 5
                    and str(item["team"]["id"]) not in current_flags
                }

                # Merge if needed
                if len(processed_data):
                    merged_dict = dict(
                        sorted({**current_flags, **processed_data}.items())
                    )

                    self.update_document(
                        "mam_teams_flags",
                        "flags",
                        {
                            "data": make_data_string(merged_dict)
                        },
                        "mam_teams_flags 01"
                    )

                return data

        except Exception as ex:
            print(f"Error in get_tol: {ex}")
            return None

    def update_live_game(self, data={}, id=None, testing=False, debug_mode=False):
        """Optimized version of update_live_game with correct document handling"""

        if debug_mode:
            print(f"\n---> update_live_game")

        # ------------------------
        # 1. FETCH TODAY’S GAMES
        # ------------------------
        doc = self.get_document(
            "mam_today_games_results",
            "today_results",
            "update_live_game 01"
        )

        # print(f"doccccccccccc {doc}")

        if not doc:
            print("❌ ERROR: today_results document missing or invalid")
            return data

        today_games = doc[0]

        if not isinstance(today_games, list):
            print("❌ ERROR: today_results.data is not a list")
            return data

        # Build dictionary: fixture_id → full fixture
        to_play_games_dict = {
            str(self.get_data_from_dict(fx, "fixture,id")): fx
            for fx in today_games
        }

        # ------------------------
        # 2. SELECT FUTURE GAMES FROM INPUT
        # ------------------------
        future_response = data.get("future", {}).get("response", [])

        if not isinstance(future_response, list):
            print("❌ ERROR: data['future']['response'] is not a list")
            return data

        update_flag = False

        # ------------------------
        # 3. UPDATE MATCHES
        # ------------------------
        for index, fixture in enumerate(future_response):

            try:
                game_id = str(fixture["fixture"]["id"])
            except Exception:
                continue

            if game_id in to_play_games_dict:
                data["future"]["response"][index] = to_play_games_dict[game_id]
                update_flag = True

        # ------------------------
        # 4. RETURN UPDATED DATA
        # ------------------------
        return data

    def get_ng(self, team_id=529, next_len=3):
        team_doc_id = f"next_games_team_{team_id}"
        team_data = None
        today = self.get_today()
        is_jwt_used = False

        print(f"\n\n[START] get_ng | team_id={team_id}, today={today}")

        # Decode data if JWT token format (long string)
        if len(str(team_id)) > 10:
            decoded = self.decode_data(team_id)
            league_id = re.sub(r"\D", "", decoded["league_id"])
            teams_len = int(decoded["teams_len"])
            team_doc_id = f"next_games_team_{decoded['league_id']}"

            print(f"[JWT MODE] league_id={league_id}, teams_len={teams_len}")

            # next_games_team_NR140 will not be recorded in DB team_data will False

            team_data = self.get_document(
                self.next_games_collection_id, team_doc_id, "get_ng 01")

            # print(f"[JWT FETCH] team_data={team_data}")

            if not team_data:
                team_data = [None, today, 0]
                print(
                    f"[JWT FETCH NEW ASSIGNAMENT] \n\tteam_data={team_data}\n\ttoday {today}")

            if team_data[0] is None or today != team_data[1]:
                print("[JWT UPDATE] Fetching new data from get_next_round()")
                new_data = self.get_next_round(league_id, teams_len)

                print(new_data)

                if not new_data["future"]["response"]:
                    print("[NO FUTURE DATA] Empty response")
                else:
                    team_data[0] = new_data
                team_data[1] = today

            is_jwt_used = True

        # Non-JWT processing
        if not is_jwt_used:
            print("[NON-JWT MODE] Fetching team_data")
            team_data = self.get_document(
                self.next_games_collection_id,
                team_doc_id,
                "get_ng 02") if team_data is None else team_data

        print(
            f"[DOC CHECK] Today={today}, team_data_date={team_data[1] if team_data else None}")

        # If no document or outdated, fetch from API
        if not team_data or today != team_data[1]:
            print(
                f"[FETCH API] Getting data from get_next_games(team_id={team_id})")
            ng_data = self.get_next_games(team_id, next_len)

            if not ng_data["future"]["response"]:
                return ("No future games found")

            ng_data = self.update_live_game(ng_data)
            doc_data = {
                "data": self.make_data_string(ng_data),
                "today": today,
                "counter": 1
            }

            try:
                print(f"[DOC CREATE] {team_doc_id}")
                result = create_document(
                    collection=self.next_games_collection_id,
                    document_id=team_doc_id,
                    data=doc_data,
                )

                if isinstance(result, str) and "already exists" in result:
                    print("[DOC EXISTS] Updating instead")
                    result = self.update_document(
                        collection=self.next_games_collection_id,
                        document_id=team_doc_id,
                        data={**doc_data, "counter": team_data[2] + 1},
                    )
                    if result.get("created"):
                        return ng_data

            except AppwriteException as e:
                if e.code == 409:
                    print("[APPWRITE 409] Conflict: Updating document")
                    result = self.update_document(
                        collection=self.next_games_collection_id,
                        document_id=team_doc_id,
                        data={**doc_data, "counter": team_data[2] + 1},
                    )
                    if result.get("created"):
                        return ng_data
                else:
                    raise

            self.mam_counter_update(True)
            return ng_data

        # Use existing internal data
        print("[USE INTERNAL] Updating from internal team_data")
        # print(team_data)
        updated_data = False

        if team_data[0] is not None:
            updated_data = self.update_live_game(team_data[0])

            # if not update_result create
            update_result = self.update_document(
                collection=self.next_games_collection_id,
                document_id=team_doc_id,
                data={
                    "data": self.make_data_string(updated_data),
                    "counter": team_data[2] + 1
                },
                by="ng with internal update"
            )

            if not update_result or ("not be found" in update_result):
                print("[DOC NOT FOUND] Recreating document")
                self.create_document(
                    collection=self.next_games_collection_id,
                    document_id=team_doc_id,
                    data={
                        "data": self.make_data_string(team_data[0]),
                        "today": today,
                        "counter": 1
                    }
                )

        self.mam_counter_update()
        return updated_data

    def get_fixture(self, fixture_id, testing=False):
        """
        returns dict data from api football API, uses get_fixture_by_id  .

        Args:
            fixture_id (int): provided by api
            testing (bool): local testing puposs
        Returns:
            dict

            next_games_team_541
        """

        fixture_id = str(fixture_id)
        current_millis = self.get_millis()
        new_data = False

        if testing:

            print("getting test data ")
            import dataFixture

            data = dataFixture.fixture

            new_data = {}

            for item in data["response"]:
                if item.get("teams", "No 'teams' key found"):
                    new_data["teams"] = item.get(
                        "teams", "No 'teams' key found")

                if item.get("goals", "No 'goals' key found"):
                    new_data["goals"] = item.get(
                        "goals", "No 'teams' key found")

                if item.get("fixture", "No 'fixture' key found"):
                    new_data["fixture"] = item.get(
                        "fixture", "No 'teams' key found")

            pprint(new_data)

        else:

            new_game_data = False
            # this_game = self.get_document("mam_fixtures_by_id", fixture_id)
            this_game = self.get_document(
                "mam_fixtures_by_id", fixture_id)

            print(f"\n\n This Game {'<>'*30}")
            pprint(this_game)

            # pprint(this_game)
            game = self.get_dict(this_game["fixture"]) if this_game else False
            game_last_update = (
                self.make_val_string(this_game["last_update_millis"])
                if game
                else self.get_millis() - 600000
            )
            game_status = (
                self.get_data_from_dict(
                    game, "fixture,status,long") if game else "pending"
            )

            if not this_game:
                print(
                    f"\nGame record does not exists will create it now id {fixture_id}")
                this_game = self.get_fixture_by_id(fixture_id)
                game_status = (
                    self.get_data_from_dict(this_game, "fixture,status,long")
                    if this_game
                    else "pending"
                )

                print(f"new game status {game_status}")

                doc = self.create_document(
                    collection="mam_fixtures_by_id",
                    document_id=fixture_id,
                    data={
                        "fixture": make_data_string(this_game),
                        "last_update_millis": make_val_string(current_millis),
                    },
                )

                if doc["created"]:
                    new_data = True
                    return this_game

            # pprint(game)
            # print(game_last_update)

            # Calculate boundaries
            if (
                self.minutes_after_last_update(
                    self.convert_to_milliseconds(
                        game_last_update, "get_fixture 02 CC"),
                    self.get_millis(),
                    600,
                )
                and game_status not in self.not_live_by_game_status
            ):

                print(
                    f"\n\n---------------\nGame record {fixture_id} needs an update")
                this_game = self.get_fixture_by_id(fixture_id)

                doc = self.update_document(
                    collection="mam_fixtures_by_id",
                    document_id=fixture_id,
                    data={
                        "fixture": self.make_data_string(this_game),
                        "last_update_millis": self.make_val_string(current_millis),
                    },
                )

                if doc["created"]:
                    return this_game

            else:
                return game

    def extract_teams_and_scores(self, data):
        """
        Extracts team names and scores from the given data.

        Args:
            data (dict): The input data containing fixture, goals, and teams information.

        Returns:
            dict: A dictionary with team names and their respective scores.
        """
        teams = [data["teams"]["home"]["name"], data["teams"]["away"]["name"]]
        scores = [data["goals"]["home"], data["goals"]["away"]]
        return {"teams": teams, "score": scores}

    def is_duplicate_id(self, option_id, document_id, record_id):
        """Check if the generated ID exists in the current IDs."""

        print(f"document_id {document_id}")
        document = self.get_document(document_id, record_id)
        if not document:
            return document
        current_ids = self.make_data_string(document["ids"])
        return option_id in current_ids

    def create_mam_id(
        self, length=8, _for="login", chars=string.ascii_uppercase + string.digits + "$"
    ):
        """
        Generate a unique MAM ID consisting of uppercase letters, digits, and the '$' symbol.

        Parameters:
            length (int): The length of the MAM ID to generate. Default is 8.
            _for (str): The context for which the ID is generated ('login' or 'saves').

        Returns:
            str: A unique MAM ID.

        Raises:
            ValueError: If an invalid context is provided for '_for'.
        """

        # Predefined document IDs
        mam_current_account_ids = "676ae5b10035cb473e22"
        mam_current_saves_ids = "mam_saves_ids"

        # characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
        characters = chars

        # Generate unique ID
        option_id = "3" + "".join(random.choice(characters)
                                  for _ in range(length))

        if _for == "bolts":
            option_id = "BOLTS" + "".join(random.choice(characters)
                                          for _ in range(length))

        if _for == "login":
            option_id = "LOG" + "".join(random.choice(characters)
                                        for _ in range(length))

        if _for == "saves":
            option_id = "ES" + "".join(random.choice(characters)
                                       for _ in range(length))

        # elif _for == "saves":
        #     print("Checking save IDs...")
        #     record_id = "all_saves_ids"
        #     while is_duplicate_id(option_id, mam_current_saves_ids, record_id):
        #         option_id = "".join(random.choice(characters) for _ in range(length))

        else:
            return option_id

        return option_id

    def update_ids(self, col, doc, account_id_created):
        cd = self.get_document(col, doc)
        # Assume cd["ids"] is a JSON string — parse it
        ids = self.get_dict(cd["ids"])  # returns dict, e.g., {"ids": [...]}

        # Append new ID
        ids["ids"].append(account_id_created)

        # 🔑 Convert back to JSON string before saving
        ids_json_str = json.dumps(ids, separators=(
            ',', ':'))  # compact, no extra spaces

        data = {"ids": ids_json_str}
        self.update_document(col, doc, data)

    def create_mam_login_two(self, data={
            "email": "test01.jandres@gmail.com",
            "user_name": "esteban",
            "password": "password",
            "referred_by": "",
        }
    ):
        """
        Returns:
            str if error (e.g., 'Email allready exists'),
            dict if success (login doc creation result)
        """
        if len(data["password"]) < 6:
            return "Password must be at least 6 characters long"

        account_id_created = self.create_mam_id(_for="login")
        email_id = self.at_id(data["email"])

        mam_login_collection_id = self.mam_login
        mam_account_ids = "676ae5b10035cb473e22"
        mam_account_doc = "676ae6120020af401e9e"

        data_to_send = {
            "user_name": data["user_name"],
            "password": data["password"],           # ✅ FIXED: was hardcoded!
            "email": data["email"],
            "account_id": account_id_created,
            "referred_by": self.make_val_string(data["referred_by"]),
            "fav_teams": self.make_data_string([]),
            "saves": self.make_data_string({"public": [], "private": []}),
            "balance": "0",
            "balance_history": self.make_data_string([]),
            "deposits": self.make_data_string(
                {
                    "pendings": [],
                    "approved": [],
                }
            ),
        }

        create_login = self.create_document(
            mam_login_collection_id, email_id, data_to_send)

        msg = (
            "Email allready exists"
            if isinstance(create_login, dict) and "generate a unique ID" in str(create_login.get("message", ""))
            else create_login
        )

        # ✅ Only proceed if creation succeeded (i.e., create_login is dict & not error)
        if isinstance(create_login, dict) and create_login.get("created"):
            try:
                self.update_ids(mam_account_ids,
                                mam_account_doc, account_id_created)
            except Exception as e:
                print(f"⚠️ update_ids failed: {e}")

            try:
                # ✅ Use a safe fallback for 'user' — e.g., 'system'
                # Since 'user' was undefined, and you said no changes, use minimal fix:
                safe_user = getattr(self, 'user', 'system')  # avoids NameError
                self.update_account_balance(
                    email=data["email"],
                    id=account_id_created,
                    update=0.0,
                    key="balance",
                    by=safe_user
                )
            except Exception as e:
                print(f"⚠️ update_account_balance failed: {e}")

        return msg

    def get_mam_account_two(self, data={
            "email": "test01.jandres@gmail.com",
            "password": "password",
            "ip": "201.247.16.251"
        }
    ):

        pprint(data)

        account = None

        # print_centered_banner(f"{'get_account'}")

        mam_login_collection_id = self.mam_login
        account = self.get_document(
            mam_login_collection_id, at_id(data["email"]))

        # print_centered_banner(f"{'in_file_bolts'}")

        in_file_bolts = self.get_document(
            "mam_bolts",
            self.at_id(data["email"]),
            "create_mam_public_escrow 01"
        )
        now = self.get_millis()

        # print(f"\n\n{account}\n\n")

        if not account:
            return "Invalid Email address"

        if account["password"] != data["password"]:
            return "Invalid Password"

        # Ensure public key is set
        if not account.get("public_key"):
            account["public_key"] = self.encode_data(
                {
                    "email": account["email"],
                    "id": account["account_id"],
                    "last_action": self.get_millis()
                }
            )

        else:
            account["public_key"] = self.encode_data(
                {
                    "email": account["email"],
                    "id": account["account_id"],
                    "last_action": self.get_millis()

                }
            )

        # print_centered_banner(f"{'update_document'}")

        d = self.update_document(
            mam_login_collection_id,
            account["$id"],
            {"public_key": account["public_key"]},
        )

        data_to_send = {}
        l = ["email", "account_id", "fav_teams",
             "saves", "public_key", "balance"]

        for key in l:
            data_to_send[key] = account[key]

        # print_centered_banner(f"{'processing data'}")

        # add fav teams next games
        added_new_public_games = False
        fav_next_games = []
        public_saves = []
        private_saves = []
        all_public_saves = []

        # print_centered_banner(f"{'processing bolts data '}")
        bolts = self.get_dict(in_file_bolts[7]) if in_file_bolts else []

        # print_centered_banner(f"{'processing get_all_public_saves data '}")

        get_all_public_saves = self.get_all_public_saves(
            ip_data={"ip": data["ip"]}, login_attempt=True)[0]
        # print(f"this is get_all_public_saves {get_all_public_saves} ")

        for team_id in get_dict(data_to_send["fav_teams"]):
            # print(f"getting data for team id {team_id}")
            fav_next_games.append(self.get_ng(team_id))

        for public in self.get_dict(account["saves"])["public"]:
            this_public_save = self.get_document("mam_public_saves", public)
            if not this_public_save:
                break
            this_public_save = this_public_save[0]
            this_public_save["creator"] = remove_at(
                this_public_save["creator"])
            del this_public_save["pay_out"]
            this_public_save["game_data"] = get_fixture(
                str(this_public_save["fixture"]))
            public_saves.append(this_public_save)

            this_fixture_id = str(this_public_save["id"])
            if this_fixture_id not in get_all_public_saves:
                get_all_public_saves[this_fixture_id] = this_public_save
                added_new_public_games = True

        # Sort dictionary by creation_date in descending order
        sorted_data = dict(
            sorted(get_all_public_saves.items(), key=lambda item: item[1]["creation_date"], reverse=True))

        # print(f"will save data {added_new_public_games}")

        if added_new_public_games:

            updated = False  # Declare outside the loop

            while not updated:
                updated_doc = self.update_document(
                    "mam_public_all",
                    "all_public_1",
                    {
                        "data": self.make_data_string(sorted_data)
                    },
                    "updating changes from login >> 310929672"
                )

                # Debugging step
                # print(f"Updated doc response: {updated_doc}")

                if updated_doc:
                    # Ensure this is correctly accessed
                    updated = updated_doc.get("created", False)

                # Debugging step
                # print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Updated: {updated}")

                time.sleep(3)

        for private in self.get_dict(account["saves"])["private"]:
            this_public_save = self.get_document("mam_private_saves", private)
            if not this_public_save:
                break
            this_private_save = this_public_save[0]
            this_private_save["creator"] = self.remove_at(
                this_private_save["creator"])
            del this_private_save["pay_out"]
            this_private_save["game_data"] = self.get_fixture(
                str(this_private_save["fixture"]))
            private_saves.append(this_private_save)

        data_to_send["fav_next_games"] = fav_next_games
        data_to_send["saves"] = {
            "public": public_saves, "private": private_saves}
        data_to_send["escrow_history"] = self.get_escrow_history(
            data["email"], account["account_id"])

        all_public_saves.append(get_all_public_saves)
        data_to_send["all_public_saves"] = all_public_saves
        data_to_send["bolts"] = bolts

        return data_to_send

    def process_escrow(
        self, public_saves, account_charges, update_balance, is_public=True, account=None
    ):
        processed_public_saves = []
        # print(f"{'-'*80}\nproccesing {'public' if is_public else 'private'} save\n\naccount details : {account}")

        for save_in_question in public_saves:
            print(f"\n\n{'*'*80}"
                  f"\nproccesing save id : {save_in_question}")
            this_public_save = self.get_document(
                "mam_public_saves" if is_public else "mam_private_saves",
                save_in_question,
                f"process_escrow {save_in_question} CC"
            )

            if not this_public_save:
                continue

            this_public_save = this_public_save[0]
            this_public_save["creator"] = self.remove_at(
                this_public_save["creator"])
            game_data = self.get_fixture(str(this_public_save["fixture"]))
            creator = this_public_save["creator"]
            taker = this_public_save["taker"]
            save_amount = float(this_public_save["save_amount"])
            winner = self.determine_winner(game_data)
            this_public_save["pay_out"]["date"] = self.get_millis()
            game_status = self.get_data_from_dict(
                game_data, "fixture,status,long")
            if game_status not in self.not_live_by_game_status:
                this_public_save["this_public_save"] = game_data
                processed_public_saves.append(this_public_save)
                continue
            balance_to_add = (save_amount * 2) * account_charges / 100
            draw_account_charges = 95
            escrow_value = save_amount * 2
            balance_to_add = (
                balance_to_add
                if winner != "draw"
                else (save_amount * 2) * draw_account_charges / 100
            )
            company_profit = escrow_value - balance_to_add
            print(
                f"\n\ncreator: {creator}"
                f"\ntaker: {taker}"
                f"\nsave amount: {save_amount}"
                f"\nStatus: {game_status}"
                f"\nsave: {this_public_save}"
                f"\nWinner: {winner}"
                f"\nEscrow Value: {escrow_value}"
                f"\nBalance to add: {balance_to_add}"
                f"\ncompany_profit to add: {company_profit}\n\n\n"
            )

            if "home" in winner or "away" in winner:
                if taker != "pending":
                    if this_public_save["creator_side"] in winner:
                        print(f"\n\nAdding balance to creator: {creator}\n\n")
                        update_balance[creator] = (
                            update_balance.get(creator, 0) + balance_to_add
                        )
                        this_public_save["pay_out"]["pay_out"] = balance_to_add
                        this_public_save["pay_out"]["save_receiver"] = creator
                        this_public_save["pay_out"]["save_payer"] = taker
                        this_public_save["pay_out"]["save_result"] = winner
                        this_public_save["game_data"] = self.extract_teams_and_scores(
                            game_data)
                        pprint(this_public_save)
                        # account = process_escrow_payout(
                        #     save_in_question, this_public_save, account, company_profit
                        # )

                    else:
                        print(f"Adding balance to taker: {taker}")
                        update_balance[taker] = (
                            update_balance.get(taker, 0) + balance_to_add
                        )
                        this_public_save["pay_out"]["pay_out"] = balance_to_add
                        this_public_save["pay_out"]["save_receiver"] = taker
                        this_public_save["pay_out"]["save_payer"] = creator
                        this_public_save["pay_out"]["save_result"] = winner
                        this_public_save["game_data"] = self.extract_teams_and_scores(
                            game_data)
                        pprint(this_public_save)
                        # account = process_escrow_payout(
                        #     save_in_question, this_public_save, account, company_profit
                        # )
                else:
                    (
                        print(
                            f"No taker, refunding full save amount to creator: {creator}")
                        if game_status in self.not_live_by_game_status
                        else print("Open Escrow")
                    )
                    update_balance[creator] = update_balance.get(
                        creator, 0) + save_amount
                    this_public_save["pay_out"]["save_receiver"] = creator
                    this_public_save["pay_out"]["save_payer"] = "Not Taken"
                    this_public_save["pay_out"]["save_result"] = "Not Taken"
                    this_public_save["pay_out"]["pay_out"] = this_public_save["save_amount"]
                    this_public_save["game_data"] = self.extract_teams_and_scores(
                        game_data)
                    pprint(this_public_save)
                    # account = process_escrow_payout(
                    #     save_in_question, this_public_save, account, company_profit
                    # )
            else:

                balance_to_split = save_amount * draw_account_charges / 100
                print(f"Split balance: {balance_to_split}")

                if taker != "pending":
                    update_balance[creator] = (
                        update_balance.get(creator, 0) + balance_to_split
                    )
                    update_balance[taker] = update_balance.get(
                        taker, 0) + balance_to_split
                    print(
                        f"Split between creator: {creator} and taker: {taker}")
                    this_public_save["pay_out"]["save_receiver"] = "Split"
                    this_public_save["pay_out"]["save_payer"] = "Split"
                    this_public_save["pay_out"]["save_result"] = "Split"
                    this_public_save["pay_out"]["save_split_emails"] = [
                        creator, taker]
                    this_public_save["pay_out"]["pay_out"] = balance_to_split
                    this_public_save["game_data"] = self.extract_teams_and_scores(
                        game_data)
                    pprint(this_public_save)
                    # account = process_escrow_payout(
                    #     save_in_question, this_public_save, account, company_profit
                    # )

                else:
                    update_balance[creator] = update_balance.get(
                        creator, 0) + save_amount
                    print(
                        f"No taker, returning full save amount to creator: {creator}")
                    this_public_save["pay_out"]["save_receiver"] = creator
                    this_public_save["pay_out"]["save_payer"] = "Not Taken"
                    this_public_save["pay_out"]["save_result"] = "Not Taken"
                    this_public_save["pay_out"]["pay_out"] = this_public_save["save_amount"]
                    this_public_save["game_data"] = self.extract_teams_and_scores(
                        game_data)
                    pprint(this_public_save)
                    # account = process_escrow_payout(
                    #     save_in_question, this_public_save, account, company_profit
                    # )

            # this line is to be removed
            processed_public_saves.append(this_public_save)

        return processed_public_saves

    def get_mam_account_three(self, data={
            "email": "test01.jandres@gmail.com",
            "password": "password",
            "returnPublicEscrow": False,
            "returnPrivateEscrow": False,
            "returnFavGames": False,
        }
    ):

        print("--- > Start of get_mam_account_three ")
        self.start_time()
        mam_login_collection_id = self.mam_login
        account = self.get_document(mam_login_collection_id, self.at_id(
            data["email"]), "get_mam_account 3-1")
        now = self.get_millis()

        if not account:
            return "Invalid Email address"

        if account["password"] != data["password"]:
            return "Invalid Password"

        if not account.get("public_key"):
            account["public_key"] = self.encode_data(
                {
                    "email": data["email"],
                    "id": data["account_id"],
                    "login": {
                        "last_request": now,
                        "seconds_to_next_request": 300,
                        "max_usage": 10,
                        "used": 0
                    },
                    "countries_list": {
                        "last_request": now,
                        "seconds_to_next_request": 600,
                        "max_usage": 3,
                        "used": 0
                    },
                    "competitions_in_countries_list": {
                        "last_request": now,
                        "seconds_to_next_request": 5,
                        "max_usage": 3,
                        "used": 0
                    },
                    "teams_in_competitions_list":  {
                        "last_request": now,
                        "seconds_to_next_request": 5,
                        "max_usage": 20,
                        "used": 0
                    },
                    "games_of_team":  {
                        "last_request": now,
                        "seconds_to_next_request": 5,
                        "max_usage": 50,
                        "used": 0
                    },
                    "update_favs":  {
                        "last_request": now,
                        "seconds_to_next_request": 5,
                        "max_usage": 30,
                        "used": 0
                    }
                }
            )

        print("aaaaaaaaaaaaaaaaaaaaaccount")
        print(account)

        account_data = self.get_dict(account["account_data"])

        self.update_document(
            mam_login_collection_id,
            account["$id"],
            {"public_key": account["public_key"]},
            "get_mam_account 3-1 CC"
        )

        data_to_send = {
            key: account[key]
            for key in [
                "email",
                "account_id",
                "fav_teams",
                "saves",
                "public_key",
                "balance",
            ]
        }
        data_to_send["lang"] = account_data["lang"] if "lang" in account_data else "en"

        data_to_send["fav_next_games"] = (
            [self.get_ng(team_id)
             for team_id in self.get_dict(data_to_send["fav_teams"])]
            if data["returnFavGames"]
            else []
        )

        account_charges = 100 - 7.5
        update_balance = {}

        # if data["returnPublicEscrow"]:
        #     print(
        #         f"\n\nPUBLIC GAMES ------------------------------------------------------------------------\n\n"
        #     )
        #     public_saves = get_dict(account["saves"])["public"]
        #     if len(public_saves):
        #         processed_public_saves = process_escrow(
        #             public_saves, account_charges, update_balance, True, account
        #         )
        #         print(f"processed_public_saves {processed_public_saves}")
        #     else:
        #         processed_public_saves = []
        # else:
        #     processed_public_saves = []

        # if data["returnPrivateEscrow"]:
        #     print(
        #         f"\n\nPRIVATE GAMES ------------------------------------------------------------------------\n\n"
        #     )
        #     private_saves = get_dict(account["saves"])["private"]
        #     if len(private_saves):
        #         processed_private_saves = process_escrow(
        #             private_saves, account_charges, update_balance, False, account
        #         )
        #         print(f"processed_private_saves {processed_private_saves}")
        #     else:
        #         processed_private_saves = []
        # else:
        #     processed_private_saves = []

        saves = self.get_dict(account["saves"])

        data_to_send["saves"] = {
            "public": saves["public"],
            "private": saves["private"],
        }
        data_to_send["escrow_history"] = self.get_escrow_history(
            data["email"], account["account_id"])
        print(f"Update balance: {update_balance}")
        self.end_time("get_mam_account_three")

        self.string_weight_in_megabits(
            self.make_data_string(data_to_send), "account")

        return data_to_send

    def update_favs(self, data={
            "email": "dres@gmail.com",
            "account_id": "3D8Y8SFFN",
            "fav_teams": "[40, 487]",
            "public_key": "3VYWLKBNNZFW$UJNELN58RKBXWO32OZX9Z5GVC",
        }
    ):

        mam_login_collection_id = self.mam_login
        account_id = self.at_id(data["email"])

        new_public_key = self.create_mam_id(random.randint(30, 90), "key")
        favs = self.update_document(
            mam_login_collection_id,
            account_id,
            {"fav_teams": data["fav_teams"], "public_key": new_public_key},
        )

        if favs["created"]:
            favs["public_key"] = new_public_key
            return favs

    def create_escrow(
        self,
        fixture_id=1208691,
        save_type="public",
        creator="test01.jandres@gmail.com",
        creator_side="home",
        save_amount=20,
        testing=False,
        is_accepting=False,
        save_id=None,
    ):
        """
        Create or accept a save for a fixture with specified parameters.
        """

        if save_type not in ["public", "private", "multiple"]:
            return {"response": "Invalid escrow type"}

        operation_type = "Accepting a Save" if is_accepting else "Creating Save"
        print(
            f"\n\n{operation_type}\n"
            f"Fixture ID: {fixture_id}\n"
            f"Save Type: {save_type}\n"
            f"Creator: {creator}\n"
            f"Save Amount: {save_amount}\n"
        )

        # Validate balance if not in testing mode
        balance = 100 if testing else self.get_account_balance(creator)
        if not testing and save_amount > balance:
            return {"response": "Insufficient balance"}

        # Fetch fixture data
        fixture_data = self.get_document(
            "mam_fixtures_by_id", str(fixture_id), "create_escrow 01CC ")
        now = self.get_millis()

        if fixture_data:
            game = self.get_dict(fixture_data["fixture"])
            game_status = self.get_data_from_dict(game, "fixture,status,long")
            last_updated = int(fixture_data.get("last_update_millis", 0))
            ten_min_update = self.minutes_after_last_update(
                last_updated, now, 600)

            if (ten_min_update and game_status not in self.not_live_by_game_status) or (
                self.get_data_from_dict(game, "fixture,periods,first")
                < now
                < self.get_data_from_dict(game, "fixture,periods,second")
            ):
                print("Refreshing fixture data...")
                fixture_data = get_fixture(str(fixture_id))
                game_status = self.get_data_from_dict(
                    fixture_data, "fixture,status,long")
        else:
            print("Fetching live fixture data...")
            game = get_fixture_by_id(str(fixture_id))
            if not game:
                return {"response": "Game ID does not exist"}
            game_status = self.get_data_from_dict(game, "fixture,status,long")

        second_period_start = self.get_data_from_dict(
            game, "fixture,periods,second"
        ) or self.convert_to_milliseconds(self.get_data_from_dict(game, "fixture,date"))
        time_since_second_period = self.minutes_after_last_update(
            second_period_start, now, 2400)
        can_protect = (
            game_status not in self.not_live_by_game_status and not time_since_second_period
        )

        print(f"Second Period Start: {second_period_start}\n")
        print(f"Time since second period: {time_since_second_period}")
        print(f"Game Status: {game_status} | Can Protect: {can_protect}\n")

        if not can_protect:
            return {"response": game_status}

        if not is_accepting and save_id is None:
            save_id = self.create_mam_id(
                17, _for="saves", chars=string.ascii_uppercase)
            save_data = {
                "fixture": fixture_id,
                "creator": creator,
                "taker": "pending",
                "creation_date": now,
                "id": save_id,
                "creator_side": creator_side,
                "save_amount": save_amount,
                "save_type": save_type,
                "save_status": "created",
                "second_period_start": second_period_start,
                "pay_out": {
                    "date": "date",
                    "save_receiver": "creator",
                    "pay_out": "amount",
                    "teams": {"home": "home", "away": "away"},
                    "goals": {"home": "home", "away": "away"},
                },
            }

            doc = self.create_document(
                f"mam_{save_type}_saves",
                str(save_id),
                data={"data": self.make_data_string(save_data)},
            )
            if isinstance(doc, str) and "already exists" in doc:
                return self.create_escrow(fixture_id, save_type, creator, save_amount)

            if doc.get("document_id"):
                user_data = self.get_document(
                    self.mam_login, self.at_id(creator))
                current_saves = self.get_dict(user_data.get("saves", {}))
                current_saves.setdefault(
                    save_type, []).append(doc["document_id"])

                update_result = self.update_document(
                    self.mam_login,
                    self.at_id(creator),
                    data={
                        "saves": self.make_data_string(current_saves),
                        "balance": str(float(balance) - float(save_amount)),
                    },
                )
                if not update_result.get("created"):
                    self.delete_document(f"mam_{save_type}_saves", save_id)
                    return {"response": "Failed to update user data"}

                return {
                    "response": True,
                    "link": f"?id={save_id}" if save_type == "private" else None,
                }
        else:
            escrow_data = self.get_document(
                f"mam_{save_type}_saves", save_id)[0]
            escrow_data["taker"] = creator

            user_data = self.get_document(
                self.mam_login, at_id(creator))
            current_saves = get_dict(user_data.get("saves", {}))
            if save_id in current_saves.get(save_type, []):
                return {"response": "Escrow in Progress"}
            current_saves.setdefault(save_type, []).append(save_id)

            update_result = self.update_document(
                self.mam_login,
                self.at_id(creator),
                data={
                    "saves": self.make_data_string(current_saves),
                    "balance": str(float(balance) - float(save_amount)),
                },
            )
            return {
                "response": (
                    "Escrow Accepted"
                    if update_result.get("created")
                    else "Failed to accept escrow"
                )
            }

    def deposit_list(self):
        deposit_list = os.getenv("deposit_list", "").split(",")

        # Remove any leading/trailing spaces
        deposit_list = [item.strip() for item in deposit_list]

        return (deposit_list)  # Output: ['USDT - Tron', 'BTC - Lightning']

    def get_tn(self, team_id=39):
        team_id = str(team_id)
        team = self.get_document("mam_team_name", team_id)
        today = self.get_today()

        print(f"\n\nteam_id: {team_id}\ntoday: {today}\n\n\n")
        # pprint(team)

        # Convert dates to datetime objects
        today_date = datetime.strptime(today, "%d-%m-%Y")
        last_update_date = datetime.strptime(
            team["last_update"] if team else today, "%d-%m-%Y"
        )

        try:
            if (
                not team
                or today_date != last_update_date
                and (today_date - last_update_date).days > 28
            ):  # Check if no data or outdated data
                tn = self.get_team_name_by_id(team_id)

                # print(f"\n\n\n\n\n\n")
                # pprint(tn)
                # print(f"\n\n\n\n\n\n")

                try:
                    # Attempt to create the document
                    print(f"Atempting to create new team name\n\n")
                    print(
                        self.create_document(
                            collection="mam_team_name",
                            document_id=team_id,
                            data={
                                "name": self.make_data_string(tn),
                                "last_update": today,
                                "counter": 1,
                            },
                        )
                    )
                except AppwriteException as e:
                    if e.code == 409:  # Conflict: Document already exists
                        # Update the existing document
                        self.update_document(
                            collection="mam_team_name",
                            document_id=team_id,
                            data={
                                "name": self.make_data_string(tn),
                                "last_update": today,
                                "counter": 1,
                            },
                        )
                    else:
                        raise  # Re-raise other exceptions

                # self.mam_counter_update(True)
                return tn
            else:

                print(f"Sending local data\n\n")

                # Update the counter in the existing document
                self.update_document(
                    collection="mam_team_name",
                    document_id=team_id,
                    data={"counter": team["counter"] + 1},
                )

                # self.mam_counter_update()
                return self.get_dict(team["name"])

        except Exception as ex:
            print(f"Error in tn: {ex}")
            return None

    def create_bolt_ids(self, email):
        # creation
        mam_id = self.create_mam_id(
            3, _for="bolts", chars=string.ascii_uppercase)
        email_part = email[:3]
        timestamp = self.get_millis()
        bolt_id = f"{mam_id}{email_part}{timestamp}".upper()

        bolt_id = bolt_id.replace('1', 'L')
        return bolt_id

    def create_mam_public_escrow(self, data={}):

        if data.get("name", None) is None:
            return {"response": "please provide the escrow name"}

        current_data = None

        # data comming from api

        email = data["email"]

        docs = self.get_document(
            "mam_bolts",
            self.at_id(email),
            "create_mam_public_escrow 01"
        )

        data["home"] = 0
        data["away"] = 0
        data["creation"] = self.get_millis()
        bolt_id = None

        if docs:
            current_data = docs[0]
            current_bolts = self.get_dict(docs[7])

            # pprint(current_data)
            # print(f"current_bolts {current_bolts}")
            # print(len(current_bolts))
            # pprint(data)

            if int(current_data["live"]) > 1 or len(current_bolts) > 1:
                return "You all ready have 2 games oppened"

            current_data["live"] = current_data["live"] + 1
            current_data["total_created"] = current_data["total_created"] + 1
            # print(current_data)

            live = current_data.get("live", 0) + 1
            # print(f"live {live}")

            bolt_id = self.create_bolt_ids(email)
            data["id"] = bolt_id
            current_bolts.append(data)
            bolts = current_bolts
            # adding new bolt to aall bolts
            pprint(bolts)

            updated_doc = self.update_document("mam_bolts", self.at_id(email), {
                "data": self.make_data_string(current_data),
                "bolts": self.make_data_string(bolts)
            })

            print(updated_doc)

            if "created" in updated_doc:
                return {"bolt": True, "data": bolts[-1]}

        else:
            print("NO EXISTING DOCS")
            bolt_id = self.create_bolt_ids(email)
            data["id"] = bolt_id
            tracker = {
                "live": 1,
                "total_created": 1,
                "total_taken": 0,
                "total_not_taken": 0,
                "total_usd": 0,
                "total_profit": 0
            }

            bolts = [data]

            created_doc = self.create_document("mam_bolts", self.at_id(email), {
                "data": self.make_data_string(tracker),
                "bolts": self.make_data_string(bolts)
            })

            print(f"this is doc creation {created_doc}")

            if "created" in created_doc:
                return {"bolt": True, "data": bolts[0]}

        # pprint(docs)
        # pprint(data)
        print(bolt_id)

    def update_bolt(self, data={}):

        key = data["key"]
        bold_id = data["bolt_id"]
        home = data["home"]
        away = data["away"]
        email = None
        decoded_key = None

        try:
            decoded_key = self.decode_data(key)
            email = decoded_key["email"]
        except Exception as e:
            return {"error_id": "0x0002", "message": "invalid key"}

        if "email" not in decoded_key:
            return "Invalid Email"

        docs = self.get_document(
            "mam_bolts",
            self.at_id(email),
            "create_mam_public_escrow 01"
        )

        if docs:

            # pprint(docs)

            c = 0
            bolts = self.get_dict(docs[7])
            current_data = self.get_dict(docs[0])
            for c, bolt in enumerate(bolts):
                if bolt["id"] == bold_id:
                    bolts[c]["home"] = home
                    bolts[c]["away"] = away

                    if data["update"] == "updateBolt":
                        updated_doc = self.update_document("mam_bolts", self.at_id(email), {
                            "bolts": self.make_data_string(bolts)
                        })
                        return {"updated": "created" in updated_doc}

                    elif data["update"] == "closeBolt":
                        historical = bolts.pop(c)
                        current_data["live"] = current_data["live"] - 1

                        current_history = self.get_dict(docs[8])
                        if not current_history:
                            history_data = [historical]
                        else:
                            history_data = current_history + [historical]

                        updated_doc = self.update_document("mam_bolts", self.at_id(email), {
                            "bolts": self.make_data_string(bolts),
                            "history": self.make_data_string(history_data),
                            "data": self.make_data_string(current_data)
                        })

                        return {"closed": "created" in updated_doc}

            # If no bolt with matching ID is found
            return "Invalid Id"

        else:
            return "Invalid Id"

    def update_bolt(self, data={}):

        key = data["key"]
        bold_id = data["bolt_id"]
        home = data["home"]
        away = data["away"]
        email = None
        decoded_key = None

        try:
            decoded_key = self.decode_data(key)
            email = decoded_key["email"]
        except Exception as e:
            return {"error_id": "0x0002", "message": "invalid key"}

        if "email" not in decoded_key:
            return "Invalid Email"

        docs = self.get_document(
            "mam_bolts",
            self.at_id(email),
            "create_mam_public_escrow 01"
        )

        if docs:

            # pprint(docs)

            c = 0
            bolts = self.get_dict(docs[7])
            current_data = self.get_dict(docs[0])
            for c, bolt in enumerate(bolts):
                if bolt["id"] == bold_id:
                    bolts[c]["home"] = home
                    bolts[c]["away"] = away

                    if data["update"] == "updateBolt":
                        updated_doc = self.update_document("mam_bolts", self.at_id(email), {
                            "bolts": self.make_data_string(bolts)
                        })
                        return {"updated": "created" in updated_doc}

                    elif data["update"] == "closeBolt":
                        historical = bolts.pop(c)
                        current_data["live"] = current_data["live"] - 1

                        current_history = self.get_dict(docs[8])
                        if not current_history:
                            history_data = [historical]
                        else:
                            history_data = current_history + [historical]

                        updated_doc = self.update_document("mam_bolts", self.at_id(email), {
                            "bolts": self.make_data_string(bolts),
                            "history": self.make_data_string(history_data),
                            "data": self.make_data_string(current_data)
                        })

                        return {"closed": "created" in updated_doc}

            # If no bolt with matching ID is found
            return "Invalid Id"

        else:
            return "Invalid Id"

    def get_bolt_icons(self, key):
        email = None

        try:
            decoded_key = self.decode_data(key)
            email = decoded_key["email"]
        except Exception as e:
            return {"error_id": "0x0002", "message": "invalid key"}

        if "email" not in decoded_key:
            return "Invalid Email"

        icons = self.get_document(
            "mam_new_bolt_icons",
            "current_bolt_icons",
            "get_bolt_icons"
        )

        # assume icons[0] is a string like "['a.png', 'b.png']"
        raw_data = icons[0]
        icons_list = self.get_dict(raw_data)

        # If it still comes out as a string, use ast.literal_eval
        if isinstance(icons_list, str):
            try:
                icons_list = ast.literal_eval(icons_list)
            except Exception as e:
                return "List not available"

        return icons_list

    def request_withdraw(self, data, get_history=False):
        """
        Handles a user's withdrawal request:
        - Decodes the provided key to extract user information.
        - Validates action timing.
        - Creates or updates the user's withdrawal document.
        """
        collection = "mam_withdraw"
        # data = {
        #     "update": "withdrawal",
        #     "key": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3QwMS5qYW5kcmVzQGdtYWlsLmNvbSIsImlkIjoiMzZaNVpOWTJaIiwibGFzdF9hY3Rpb24iOjE3NDE5NTUwNjM4NzF9.h3ABrFDqrj-Cjz2M30MLQZqUbc2wnoI45ZiWUg_rHlERo6rsEIwmcJaXf1KEAkH8cQ4wNrMtTK8NJrGjSQTv7UIesEeh5ly5ocIhMXLq7BUdbEUSYvo6jO-lgn-uAIADITL8FpkSTdd8Dv18Zu0ZisoYYZv0wtSuFYYg5Po",
        #     "document_id": "UYRP5H7G7BC4DAGGIMMW3F0PJDCRL8A",
        #     "collection": "3MMX72FR455QGXY5L64NB3YQJ1LH",
        #     "amont": 40,
        # }

        # Validate input data
        required_fields = ["key", "document_id", "collection", "amont"]
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"

        try:
            uncoded_key = self.decode_data(data["key"])
            email = uncoded_key["email"]
            last_action = uncoded_key["last_action"]

            print(f"uncoded key {uncoded_key}")
        except Exception as e:
            return f"Error: invalid key - {e}"

        # if not self.can_continue_by_time(last_action):
        #     return "Please wait before making another withdrawal request."

        doc_id = self.at_id(email)
        current_w_request = self.get_document(
            collection, doc_id, "account_id_valid CC 01")

        if not current_w_request:
            # First-time request
            data_to_save = [[data], []]
            new_doc = self.create_document(
                collection,
                doc_id,
                {"data": self.make_data_string(data_to_save)}
            )

            if new_doc.get("created"):
                return "Your withdrawal request has been received and is being processed."
            return "Failed to create new withdrawal request."

        # Existing request found
        pending_w_request, history_w_request = current_w_request[0]

        if get_history:
            return history_w_request

        pending_w_request.append(data)
        updated_data = [pending_w_request, history_w_request]

        updated_doc = self.update_document(
            collection,
            doc_id,
            {"data": self.make_data_string(updated_data)}
        )

        return updated_doc

    # ----------------------------------------------------------
    # Helper to create base body
    # ----------------------------------------------------------

    def make_ip_base_controller(self, name, ip, current_millis, calls_in_error, time_controller):
        return {
            name: {
                "last_update": current_millis,
                "error_calls": [0, calls_in_error, time_controller]
            },
            "ipAddress": ip,
        }

    def check_ip_exists(self, data={}, testing=False):

        if testing:
            return {'blocked': False, 'code': 200}

        key = self.ip_encode_key
        raw_ip = data["ip"]
        current_millis = self.get_millis()
        calls_in_error = int(os.getenv("calls_in_error"))
        ip_table = "mam_not_logged_in_ip_control"
        token = None
        # Encode the IP
        encoded_ip = self.encode_decode_36(raw_ip, key, True)
        time_controller = self.get_timer("ipChanged")

        # if key not in data it maybe a first contact
        if "key" in data:
            token = self.decode_data(data["key"])
            token_ip = token["ipAddress"]

            print(f"\n\ntoken \n\n")
            pprint(token)
            print(f"\n\n{token_ip}")
            print(raw_ip)

            if token_ip == raw_ip:

                # for testing
                print(f"\n\nexisting token IF {token}")
                return {
                    "blocked": True,
                    "message": f"Band",
                    "code": 1001
                }

            else:

                print(f"\n\nexisting token ELSE {token}")

                token["ipChanged"] = {
                    "last_update": current_millis,
                    "error_calls": [0, calls_in_error, time_controller]
                }

                return {
                    "blocked": True,
                    "message": f"Band",
                    "code": 1001
                }

        # Retrieve stored IP record
        ip_record = self.get_document(ip_table, encoded_ip)

        if ip_record:
            decoded_record = self.decode_data(ip_record[0])
            print("records -----------------")
            print(decoded_record)

            if data["update"] not in decoded_record:
                timer = self.get_timer(data["update"])
                body = self.make_ip_base_controller(
                    data["update"], raw_ip, current_millis, calls_in_error, timer
                )

                decoded_record[data["update"]] = body[data["update"]]

                # return decoded_record

            response = self.ip_counter_controller(
                decoded_record, data["update"])
            print("response from ip_counter_controller:", response)
            return response

        # If no record exists → create one
        timer = self.get_timer(data["update"])
        body = self.make_ip_base_controller(
            data["update"], raw_ip, current_millis, calls_in_error, timer
        )

        # Create new document

        for attempt in range(1, 6):

            print(f"Body check_ip_exists {attempt}  ")
            pprint(body)

            new_doc = self.create_document(
                ip_table,
                encoded_ip,
                {"data": self.encode_data(body)}
            )

            # ---- FIX: Guard against None or wrong type ----
            if not isinstance(new_doc, dict):
                print(
                    f"ERROR: create_document() returned NON-dict value attempt {attempt}")
                return {
                    "blocked": False,
                    "code": 500,
                    "error": "create_document returned invalid type"
                }

            # Now safe to check keys
            if new_doc.get("created") is True:
                return {
                    "blocked": False,
                    "code": 200,
                    "document_id": new_doc.get("document_id")
                }

        # Fallback return
        return new_doc

    def encode_decode_36(self, input_value: str, key: bytes, encode=True):

        ALPHABET = os.getenv("ALPHABET")

        def to_base63(b: bytes):
            n = int.from_bytes(b, "big")
            if n == 0:
                return ALPHABET[0]
            out = []
            while n > 0:
                n, r = divmod(n, 61)
                out.append(ALPHABET[r])
            return ''.join(reversed(out))

        def from_base63(s: str):
            n = 0
            for c in s:
                n = n * 63 + ALPHABET.index(c)
            bl = (n.bit_length() + 7) // 8
            return n.to_bytes(bl, "big")

        if encode:
            text = input_value

            # Encrypt
            iv = hashlib.sha256(text.encode()).digest()[:16]
            padder = padding.PKCS7(128).padder()
            padded = padder.update(text.encode()) + padder.finalize()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv),
                            backend=default_backend())
            ct = cipher.encryptor().update(padded) + cipher.encryptor().finalize()
            encrypted = iv + ct

            # Compress → encode
            compressed = zlib.compress(encrypted, 9)
            base = to_base63(compressed)

            # Add checksum
            chk = to_base63(zlib.crc32(compressed).to_bytes(4, "big"))[-2:]

            out = (base + chk)
            out = out[:36].ljust(36, "_")  # exact 36 chars
            return out

        else:
            token = input_value.rstrip("_")
            payload, chk = token[:-2], token[-2:]

            compressed = from_base63(payload)
            calcchk = to_base63(zlib.crc32(compressed).to_bytes(4, "big"))[-2:]

            if chk != calcchk:
                raise ValueError("Checksum mismatch (corrupted or wrong key)")

            decrypted = zlib.decompress(compressed)
            iv, ct = decrypted[:16], decrypted[16:]

            cipher = Cipher(algorithms.AES(key), modes.CBC(iv),
                            backend=default_backend())
            padded = cipher.decryptor().update(ct) + cipher.decryptor().finalize()

            unpadder = padding.PKCS7(128).unpadder()
            return (unpadder.update(padded) + unpadder.finalize()).decode()

    def get_timer(self, looking_for):

        timer = {
            "createEscrow": self.one_hour_control,
            "nextGames": self.one_minute,
            "getTeamOfLeague": self.one_minute,
            "allPublic": self.one_hour_control,
            "leaguesByCountry": self.one_minute,
            "getAddress": self.one_hour_control,
            "ipChanged": self.one_hour_control

        }

        return timer[looking_for]

    def ip_counter_controller(self, data, control="getAddress"):
        print("\n\n ------------------------\n\n")
        pprint(data)

        ip_control_table = "mam_not_logged_in_ip_control"
        calls_in_error = int(os.getenv("calls_in_error"))
        current_millis = self.get_millis()
        key = self.ip_encode_key

        current_ip = self.encode_decode_36(data["ipAddress"], key, True)

        last_update = data[control]["last_update"]
        error_current, error_limit, wait_window = data[control]["error_calls"]

        seconds_passed = (current_millis - last_update) / 1000
        print(f"Seconds passed: {seconds_passed}")

        # 1️⃣ RESET if cooling period passed
        if seconds_passed > wait_window:
            print("Cooldown expired → resetting counter")
            error_current = 0

        # 2️⃣ BLOCK BEFORE incrementing
        if error_current >= error_limit:
            wait_min = wait_window / 60
            return {
                "blocked": True,
                "message": f"Too many requests. Wait {wait_min:.1f} minutes.",
                "code": 1000
            }

        # 3️⃣ Increment AFTER checking block
        error_current += 1
        print(f"Updated error count → {error_current}")

        # 4️⃣ Save updates to DB
        updated_body = data.copy()
        updated_body[control]["error_calls"] = [
            error_current,
            error_limit,
            wait_window
        ]
        updated_body[control]["last_update"] = current_millis

        self.update_document(
            ip_control_table,
            current_ip,
            {"data": self.encode_data(updated_body)}
        )

        return {
            "blocked": False,
            "code": 200
        }


def check_ip_exists(data, testing):
    api = Main()
    return api.check_ip_exists(data, testing)


def request_withdraw(data=None):
    api = Main()
    get_history = False

    if data is None:
        get_history = data["get_history"]
    return api.request_withdraw(data, get_history)


def get_bolt_icons(key):
    api = Main()
    return api.get_bolt_icons(key)


def string_weight_in_megabits(text: str, name: str) -> float:
    api = Main()
    return api.string_weight_in_megabits(text, name)


def get_millis():
    api = Main()
    return api.get_millis()


def at_id(email):
    api = Main()
    return api.at_id(email)


def remove_at(email):
    api = Main()
    return api.remove_at(email)


def remove_empty(email):
    api = Main()
    return api.remove_at(email)


def start_time():
    api = Main()
    api.start_time()


def end_time(function=None):
    api = Main()
    return api.end_time(function)


def determine_winner(game):
    api = Main()
    return api.determine_winner(game)


def convert_to_milliseconds(timestamp, by=None):
    api = Main()
    return api.determine_winner(timestamp)


def minutes_after_last_update(first_millis, second_millis, seconds=60):
    api = Main()
    return api.minutes_after_last_update(first_millis, second_millis, seconds)


# minutes_after_last_update("1736617637278", "1736618570415", 600)


def encode_data(data_to_encrypt):
    api = Main()
    return api.encode_data(data_to_encrypt)


# e = encode_data({"test": "maria"})


def decode_data(encoded):
    api = Main()
    return api.decode_data(encoded)


# print(decode_data(e))


def get_data_from_dict(data={}, path="fixture,status,long"):
    api = Main()
    return api.get_data_from_dict(data, path)


# get_data_from_dict()

def make_data_string(target):
    api = Main()
    return api.make_data_string(target)


def make_val_string(target):
    api = Main()
    return api.make_val_string(target)


def get_dict(target):
    api = Main()
    return api.get_dict(target)


def mam_counter_update(external=False):
    api = Main()
    return api.mam_counter_update(external)


def convert_to_human_date(timestamp):
    api = Main()
    return api.convert_to_human_date(timestamp)


# convert_to_human_date(1736969400)


def get_today():
    api = Main()
    return api.get_today()


# print(get_millis())


# appwrite --------------------------------------------------------
def update_document(collection="xxx", document_id=None, data={}, by=None):
    api = Main()
    return api.update_document(collection, document_id, data, by)


def create_document(collection="xxx", document_id=None, data={}):
    api = Main()
    return api.create_document(collection, document_id, data)


def get_document(collection="xxx", document_id=None, by=None):
    api = Main()
    return api.get_document(collection, document_id, by)


# pprint(get_document("mam_history", "test01.jandresATgmail.com"))


def get_all_public_saves(ip):
    api = Main()
    return api.get_all_public_saves(ip)


def delete_document(collection="xxx", document_id=None):
    api = Main()
    return api.delete_document(collection, document_id)


def get_account_balance(email, id, key, by):
    api = Main()
    return api.get_account_balance(email, id, key, by)


def update_account_balance(email, id, update, key, by):

    api = Main()
    return api.update_account_balance(email, id, update, key, by)


# pprint(update_account_balance())


def get_escrow_history(email="test01.jandres@gmail.com", account_id=None, is_testing=False):
    api = Main()
    return api.get_escrow_history(email, account_id, is_testing)


# pprint(get_escrow_history(account_id="36Z5ZNY2Z", is_testing=False))


# escrow management internal history  --------------------------------------------------------


# api footbal -----------------------------------------------------


def get_tn(team_id=39):
    api = Main()
    return api.get_tn(team_id)


# pprint(get_tn())


def get_standings(league=39):
    api = Main()
    return api.get_standings(league)


# pprint(get_standings())


def get_next_round(league_id=2, teams_len=20):

    api = Main()
    return api.get_next_round(league_id, teams_len)


# pprint (get_next_round("NR3"))  # 39


def get_leagues_by_country():
    api = Main()
    return api.get_leagues_by_country()


# pprint(get_leagues_by_country())


def get_teams_of_league(league_id, season):
    api = Main()
    return api.get_teams_of_league(league_id, season)


# pprint(get_teams_of_league(39, 2024))


def get_next_games(team_id=50, next_len=3):
    api = Main()
    return api.get_next_games(team_id, next_len)


# pprint(get_next_games(529, 2))


def fetch_games(for_date, liveRequest=False, printRecords=False):
    api = Main()
    return api.fetch_games(for_date, liveRequest, printRecords)


def today_games(liveRequest=False, printRecords=False):
    api = Main()
    return api.today_games(liveRequest, printRecords)


# print(today_games())


def get_fixture_by_id(fixture_id):
    api = Main()
    return api.get_fixture_by_id(fixture_id)


# pprint(get_fixture_by_id("1318845"))


def get_team_name_by_id(team_id):
    api = Main()
    return api.get_team_name_by_id(team_id)


# print(get_team_name_by_id(33))


def get_lbc(data):
    api = Main()
    return api.get_lbc(data)


# get_lbc()


def get_tol(league_id=40):
    api = Main()
    return api.get_tol(league_id)


# pprint(get_tol())


def update_live_game(data={}, id=None, testing=False, debug_mode=False):
    api = Main()
    return api.update_live_game(data, id, testing, debug_mode)


def get_ng(team_id=40, next_len=3):
    api = Main()
    return api.get_ng(team_id, next_len)


# europa league
# print(get_ng("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJsZWFndWVfaWQiOiJOUjMiLCJ0ZWFtc19sZW4iOjM4LjB9.ersCZZrAtJKsrku981gl5ftVsBHOJGC375W5vcgnWYNnn-wblLylGRQnn1n6jwslIneFzpnb2jSF_DiwwOShG1rzEezwwno7ixm-D2sycnv5y3IsksvGFLDzLbu8wOqxuM74OsSkCj9hBwGns3mciojKbzpmb_rMTEkJDak", 1))

# conference
# print(get_ng("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJsZWFndWVfaWQiOiJOUjg0OCIsInRlYW1zX2xlbiI6ODIuMH0.mBsZ4ghUm4VB-zfVNUYIWLo9iaESAm5JXiOxJUEEc42DGi94Z2u5nr3gK1q8QR6OVlrPWpxUYH23yn_iavVPqJ-HyKYnGcWRysAFON9b4Fqp0cPlWykC03sAaMS8zoSz6-oDoFPUyD3azyW4sbEIx5-IGwwDQP7jckWp4b4", 1))


# ucl
# pprint(get_ng("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJsZWFndWVfaWQiOiJOUjMiLCJ0ZWFtc19sZW4iOjM4LjB9.ersCZZrAtJKsrku981gl5ftVsBHOJGC375W5vcgnWYNnn-wblLylGRQnn1n6jwslIneFzpnb2jSF_DiwwOShG1rzEezwwno7ixm-D2sycnv5y3IsksvGFLDzLbu8wOqxuM74OsSkCj9hBwGns3mciojKbzpmb_rMTEkJDak", 1))
# print(get_ng(50, 3))
# team_id = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJsZWFndWVfaWQiOiJOUjM5IiwidGVhbXNfbGVuIjoxMC4wfQ.O-cwE6tLb7FtSEIkrMxSUx-h1PtSP9eQFelwNJwBt-xa88NKlWrgLoL_FXlYIf6l44YCL_GzmsZCpKpEgB2J_hRmwdGMWaFHZ_GWtYD68giI3Ft8pKA0EOM9oVWZrvEMdn_Mg5QW4PVxHZLEU_5nJGTmNVZO6_ptrpWoHQo"
# data = decode_data(team_id)
# league_id = data["league_id"]
# teams_len = int(data["teams_len"])
# print(f"\n\nleague_id  {league_id} teams_len {teams_len}\n\n")
# get_ng(team_id)
# pprint(get_ng(league_id, teams_len))


def get_fixture(fixture_id, testing=False):
    api = Main()
    return api.get_fixture(fixture_id, testing)


# pprint(get_fixture(1208669))


def extract_teams_and_scores(data):

    api = Main()
    return api.extract_teams_and_scores(data)


# pprint(extract_teams_and_scores(get_fixture(1318845)))

# login  --------------------------------------------------


def is_duplicate_id(option_id, document_id, record_id):
    api = Main()
    return api.is_duplicate_id(option_id, document_id, record_id)


def create_mam_id(
    length=8, _for="login", chars=string.ascii_uppercase + string.digits + "$"
):

    api = Main()
    return api.create_mam_id(length, _for, chars)


def update_ids(col, doc, account_id_created):

    api = Main()
    return api.update_ids(col, doc, account_id_created)


def create_mam_login_two(
    data={
        "email": "test01.jandres@gmail.com",
        "user_name": "esteban",
        "password": "password",
        "referred_by": "",
    }
):

    api = Main()
    return api.create_mam_login_two(data)


def get_mam_account_two(
    data={
        "email": "test01.jandres@gmail.com",
        "password": "password",
    }
):

    api = Main()
    return api.get_mam_account_two(data)


def process_escrow(
    public_saves, account_charges, update_balance, is_public=True, account=None
):

    api = Main()
    return api.process_escrow(public_saves, account_charges, update_balance, is_public, account)


def get_mam_account_three(
    data={
        "email": "test01.jandres@gmail.com",
        "password": "password",
        "returnPublicEscrow": False,
        "returnPrivateEscrow": False,
        "returnFavGames": False,
    }
):

    api = Main()
    return api.get_mam_account_three(data)


# (
#     pprint(
#         get_mam_account_three(
#             {
#                 "email": "test01.jandres@gmail.com",
#                 "password": "password",
#                 # "returnPublicEscrow": True,
#                 # "returnPrivateEscrow": True,
#                 "returnFavGames": True,
#             }
#         )
#     )
#     if True
#     else get_mam_account_three(
#         {
#             "email": "test01.jandres@gmail.com",
#             "password": "password",
#             # "returnPublicEscrow": True,
#             # "returnPrivateEscrow": True,
#             "returnFavGames": True,
#         }
#     )
# )


def update_favs(
    data={
        "email": "test01.jandres@gmail.com",
        "account_id": "3D8Y8SFFN",
        "fav_teams": "[40, 487]",
        "public_key": "3VYWLKBNNZFW$UJNELN58RKBXWO32OZX9Z5GVC",
    }
):

    api = Main()
    return api.update_favs(data)


# pprint(update_favs())


def create_escrow(
    fixture_id=1208691,
    save_type="public",
    creator="test01.jandres@gmail.com",
    creator_side="home",
    save_amount=20,
    testing=False,
    is_accepting=False,
    save_id=None,
):

    api = Main()
    return api.create_escrow(fixture_id, save_type, creator, creator_side, save_amount, testing, is_accepting, save_id)


# pprint(
#     create_escrow(
#         fixture_id=1208691,
#         save_type="public",
#         creator="test.jandres@gmail.com",
#         creator_side="home",
#         save_amount=20,
#         testing=False,
#         is_accepting=True,
#         save_id="3NMDTRTPRGUSSRGYMP",
#     )
# )

# print(
#     create_escrow(
#         fixture_id=1299111,  # 1208253
#         save_type="public",
#         creator="test.jandres@gmail.com",
#         creator_side="home",
#         save_amount=20,
#         testing=True,
#         is_accepting=False,
#         save_id="3QUYDRQOLXXASOODUE",
#     )
# )


# x = update_document("mam_history", "estebanATgmail.com"), {"data": []}
# print(x)


def deposit_list():
    api = Main()
    return api.deposit_list()


# ********************************************************************************************************
# ********************************************************************************************************
# ********************************************************************************************************


def get_new_tron_addres(data, is_testing=False):
    wallet = Main()
    new_wallet = wallet.get_infile_tron_address_info(data, is_testing)

    if new_wallet:

        return {
            "name": "USDT - Tron Network",
            "message": "Our system will check the balance of the address and add it to your account, any amount lower than 100 USDT or not TRON NETWORK will be lost for good ",
            "min": "100",
            "max": "10,000",
            "address": new_wallet["address"],
            "img": wallet.get_qr(new_wallet["address"])
        }

    else:
        return {"error ": "Invalid account", "code": "1"}


def get_usdt_balance(address):
    wallet = Main()
    return wallet.get_usdt_balance(address)


def get_trx_balance(address):
    wallet = Main()
    return wallet.get_trx_balance(address)


def get_qr(address):
    wallet = Main()
    return wallet.get_qr(address)


def subscribe_webhook(key, secret):
    wallet = Main()
    return wallet.subscribe_webhook(key, secret)


def update_webhook(key, data):
    wallet = Main()
    return wallet.update_webhook(key, data)


def get_btc_invoice(host, store_id, amount, email, account_id, payment_id):
    wallet = Main()
    return wallet.createInvoiceD(host, store_id, amount, email, account_id, payment_id)


def get_btc_invoice_by_id(host, store_id, id):
    wallet = Main()
    return wallet.get_btc_invoice_by_id(host, store_id, id="JfsK4ddRUgDmvAHRBvLVGa")


def get_usdt_balance_free_call(address):
    wallet = Main()
    return wallet.get_balance_usdt_free_api(address)


def get_btc_lightning_address(email, id, amount, key):
    wallet = Main()
    invoice = wallet.get_infile_strike_id(email, id, amount, True, key)

    if isinstance(invoice, (dict)):
        print("\n\nResponse 01 \n------------------------------\n\n")
        print(invoice)
        return {
            "name": "BTC Lightning",
            "message": "This code will expire after 60 seconds",
            "min": "10",
            "max": "100,000",
            "address": invoice["lnInvoice"],
            "img": get_qr(invoice),
            "id": invoice["invoiceId"]
        }

    print("\n\nResponse 02 \n------------------------------\n\n")
    pprint(invoice)
    return {
        "name": "BTC Lightning",
        "message": "This code will expire after 60 seconds",
        "min": "10",
        "max": "100,000",
        "address": invoice["lnInvoice"],
        "img": get_qr(invoice)
    }


def get_usdt_transactions(address):
    wallet = Main()
    return wallet.get_usdt_transactions(address)


def validate_tron_address(address):
    wallet = Main()
    return wallet.validate_tron_address(address)


def generate_qr(email, id, content, key):
    wallet = Main()
    return wallet.gen_qr(email, id, content, key)


def get_mam_lightning_status(email, id, ticket, key):
    wallet = Main()
    return wallet.get_mam_lightning_status(email, id, ticket, key)


def create_mam_public_escrow(data):
    wallet = Main()
    return wallet.create_mam_public_escrow(data)


def update_mam_bolt(data):
    wallet = Main()
    return wallet.update_bolt(data)


if __name__ == "__main__":
    m = Main()

    ip = {
        "ip": "2800:b20:111c:224:7d61:5117:6746:1e4",
        "network": "2800:b20:111c::/48",
        "version": "IPv6",
        "city": "San Salvador",
        "region": "San Salvador Department",
        "region_code": "SS",
        "country": "SV",
        "country_name": "El Salvador",
        "country_code": "SV",
        "country_code_iso3": "SLV",
        "country_capital": "San Salvador",
        "country_tld": ".sv",
        "continent_code": "NA",
        "in_eu": False,
        "postal": None,
        "latitude": 13.6927,
        "longitude": -89.1917,
        "timezone": "America/El_Salvador",
        "utc_offset": "-0600",
        "country_calling_code": "+503",
        "currency": "USD",
        "currency_name": "Dollar",
        "languages": "es-SV",
        "country_area": 21040,
        "country_population": 6420744,
        "asn": "AS14754",
        "org": "TELECOMUNICACIONES DE GUATEMALA, SOCIEDAD ANONIMA"
    }
    millis = 1764799193439
    user = "creation11"
    email = f"{user}@gmail.com"
    fixture = "1318845"

    live_test = {'collection': '3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH',
                 'document_id': 'UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A',
                 'email': 'creation10@gmail.com',
                 'id': 'LOG87TK3VN2',
                 'ip': '2a09.bac3.556f.e78..171.575',
                 'key': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJsZWFndWVzQnlDb3VudHJ5Ijp7Imxhc3RfdXBkYXRlIjoxNzY1OTgzMjEzMzU3LCJlcnJvcl9jYWxscyI6WzAsNSw2MF19LCJpcEFkZHJlc3MiOiIyYTA5LmJhYzMuNTU2Zi5lNzguLjE3MS4yNTIifQ.OkP1mHQPxQI_3C7kpZ87B1UXJcK4iOfujIqNa9kfyUpJZk36OMkzUW4XiZl5u_NdR1eZSgxPbWg25K0RmRMJoYXah5tzL2rU4ew64-3lubFPaevR21NNHRfDGhelQaFZNX3EiwblU2EgKyHk0m_fQPKgo72Lfpxpz7qmqkc',
                 'type': 'USDT - Tron',
                 'update': 'leaguesByCountry'}

    # pprint(get_new_tron_addres(live_test))
    # result = check_ip_exists(live_test, False)
    # print("CALLER RESULT:")
    # pprint(result)

    # print(get_lbc(live_test))
