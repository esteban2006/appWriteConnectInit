from jwt.exceptions import InvalidKeyError
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError
from pprint import pprint
import os
import requests
import json
import random
import string
import jwt


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


class StrikeWallet:

    def __init__(self):
        self.url = "https://api.strike.me/v1/invoices"
        self.key = os.getenv("strike_key")

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

    def generate_id(self):
        return f"{''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(40))}"

    def issue_invoice(self, amount, user_key=None, requested_by=None):
        """

        Issues an invoice using the Strike API.
        Args:
            amount (float or str): The amount for the invoice in USDT.
            user_key (str, optional): A unique identifier for the user or purchase. 
                Defaults to None.
        Returns:
            dict: A dictionary containing the response from the Strike API, which 
            includes details such as the invoice ID, state, and other metadata.
        Raises:
            requests.exceptions.RequestException: If the HTTP request to the Strike 
            API fails.
        Example:
            invoice = self.issue_invoice(amount=20.00, user_key="user123")
            print(invoice)

        {'amount': {'amount': '20.00', 'currency': 'USDT'},
        'correlationId': '2KGRO41M7K383372CXIG9E3M9ALW58CGF242UREM',
        'created': '2024-07-29T19:23:52.7895579+00:00',
        'description': 'Simple Charts',
        'invoiceId': 'aae7e5ca-7b8d-424a-a86d-579ac44ccedc',
        'issuerId': '6d0ca2af-3009-41ee-80d1-d9566e83d418',
        'receiverId': '6d0ca2af-3009-41ee-80d1-d9566e83d418',
        'state': 'UNPAID'}

        """

        url = f"{self.url}"

        payload = json.dumps(
            {
                "correlationId": f"{self.generate_id()}",
                "description": f"{requested_by} id {user_key}",
                "amount": {
                    "currency": "USDT",
                    "amount": f"{amount}"
                },
            }
        )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.key}",
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        invoice = response.json()
        return invoice

    def get_lightning_deposit_address(self, amount, user_key="test01@gmail.com", requested_by=None):
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

        print(f"user key {user_key}")

        if "@" not in user_key:
            try:
                user_key = self.decode_data(user_key)
                # pprint(user_key)

            except Exception as e:
                return "Invalid token"
        user_key = self.encode_internal(
            {
                "email": user_key,
            }
        )

        data = self.issue_invoice(amount, user_key, requested_by)

        invoiceId = data["invoiceId"]
        url = f"{self.url}/{invoiceId}/quote"
        payload = json.dumps({})

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.key}",
        }
        response = requests.request(
            "POST", url, headers=headers, data=payload).json()

        # add invoiceId to the db
        response["invoiceId"] = invoiceId

        return response

    def get_invoice_strike_by_id(self, id):

        url = f"{self.url}/{id}"

        payload = {}
        headers = {
            'Accept': 'application/json',
            "Authorization": f"Bearer {self.key}",
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        return (response.json())

    def cancel_invoices(self, id):

        url = f"{self.url}/{id}/cancel"

        payload = {}
        headers = {
            'Accept': 'application/json',
            "Authorization": f"Bearer {self.key}",
        }

        response = requests.request(
            "PATCH", url, headers=headers, data=payload)

        return response.json()


def create_invoice(amount, user_key=None, requested_by=None):
    s = StrikeWallet()
    invoice = s.get_lightning_deposit_address(amount, user_key, requested_by)
    return invoice


def get_invoice_by_id(id):
    s = StrikeWallet()
    invoice = s.get_invoice_strike_by_id(id)
    return invoice


def cancel_invoices(id):
    s = StrikeWallet()
    invoice = s.cancel_invoices(id)
    return invoice


if __name__ == "__main__":
    pass
    # pprint(create_invoice(20.00, "user123@gmail.com", "testing team"))
    # pprint(get_invoice_by_id(id="907dd73a-c774-4303-8a0c-c7d8afb390b0"))
    # pprint(cancel_invoices(id="907dd73a-c774-4303-8a0c-c7d8afb390b0"))
