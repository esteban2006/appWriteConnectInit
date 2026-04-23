import os
import base58
import base64
import requests
import json
import jwt
from jwt.exceptions import InvalidKeyError
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError
from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.keys import PrivateKey
from pprint import pprint

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


class TronWallet:

    def __init__(self):
        api_key = os.getenv("tron_api_one")
        self.client = Tron(provider=HTTPProvider(api_key=api_key))
        self.USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
        self.API_URL_BASE = 'https://api.trongrid.io/'
        self.METHOD_BALANCE_OF = 'balanceOf(address)'

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

        # in use

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

    # in use
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

    def create_tron_wallet(self, user_key="shoulbe and email"):
        """user_key should be an email to token

        Returns:
            _type_: _description_
        """

        print(f"user key {user_key}")
        print(f"user key len : {len(user_key)}")

        if len(user_key) > 50:
            try:
                user_key = self.decode_data(user_key)
                print(f"user_key 01 {user_key} ")

            except Exception as e:

                try:
                    user_key = self.decode_internal(user_key)
                    print(f"user_key 02 {user_key} ")

                except Exception as e:
                    print(e)
                    return "Invalid token"

        for _ in range(3):

            wallet_info = self.client.generate_address_with_mnemonic()
            wallet = wallet_info[0]
            wallet["seed"] = wallet_info[1]
            valid = self.validate_tron_address(wallet["base58check_address"])
            if "result" in valid and valid["result"]:
                return wallet

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

    def address_to_parameter(self, addr):
        return "0" * 24 + base58.b58decode_check(addr)[1:].hex()

    def get_usdt_balance(self, address="ADDRESS"):
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
            # print(data['constant_result'])
            val = data['constant_result'][0]
            balance = int(val, 16) / 1000000
            print('balance =', balance)
            return float(balance)
        else:
            print('error:', bytes.fromhex(data['result']['message']).decode())

    def get_trx_balance(self, address):
        url = f"https://api.trongrid.io/v1/accounts/{address}"

        response = requests.get(url)
        data = response.json()

        if "data" in data and len(data["data"]) > 0:
            balance = data["data"][0].get(
                "balance", 0) / 1_000_000  # Convert SUN to TRX
            return balance
        else:
            return 0  # No balance or account not found


def create_tron_wallet(test_token):
    t = TronWallet()
    return t.create_tron_wallet(test_token)


def get_usdt_balance(address):
    t = TronWallet()
    return t.get_usdt_balance(address)


if __name__ == "__main__":
    test_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3QwMS5qYW5kcmVzQGdtYWlsLmNvbSJ9.DveFuC8G59RQIHxMkyxmXufO8u4bEHOKnLppZb1Hly4rG4P6xei4KRpyLfKcHWGKEhVVPzpHb09oPOTCFzekVFDyVdlq5L4WrnFjDCjgdqWApBJlnqZlME4v802bW35tyMi3Ftr7hUSv6EluhUHQMEuoevywXnLR39YjohY"
    sender_address = 'TDWccSenTzjg1PQ7AXCCBBjcLnHb8SwiZW'
    t = TronWallet()
    # pprint(create_tron_wallet(test_token))
    # pprint(t.get_usdt_transactions(sender_address))
    # print(t.get_usdt_balance(sender_address))
    # print(t.validate_tron_address(sender_address))
    # print(t.get_trx_balance(sender_address))
