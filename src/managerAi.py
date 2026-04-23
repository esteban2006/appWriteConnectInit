# from encodings.punycode import T
# from turtle import update
# from winreg import OpenKey

from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError
from jwt.exceptions import InvalidKeyError
import segno
from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.keys import PrivateKey
import base58
import base64
from datetime import datetime
import re
import json
import random
import string
import sys
import time
import re
import requests
import jwt
import copy
import os
import io
from email_server import *
from tron_wallet import *
from strike_wallet import *


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

        self.client = Tron(HTTPProvider(api_key=os.getenv("tron_api_one")))
        self.client = Tron()
        self.USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
        self.API_URL_BASE = 'https://api.trongrid.io/'
        self.METHOD_BALANCE_OF = 'balanceOf(address)'

        # update controls ------------------------------------------
        self.is_balance_being_updated = False

    # manual control ---------------------------------------------------------------------------------

    def account_exists(self, token):

        try:

            decoded_token = self.decode_data(token)
            print(f"-- > decoded token {decoded_token}")
            email = decoded_token.get("email", None)
            if email is None:
                return "Invalid Email"

            account_exits = False if not self.get_document(
                "manager_login", self.at_id(email)) else True

            if not account_exits:
                return "Invalid Account"

        except Exception as e:
            if "Invalid " in str(e):
                return "Invalid token"

        return True

    # in use
    def gen_qr(self, data):
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

    def is_duplicate_id(self, option_id, document_id, record_id):
        """Check if the generated ID exists in the current IDs."""

        print(f"document_id {document_id}")
        document = self.get_document(document_id, record_id)
        if not document:
            return document
        current_ids = self.make_data_string(document["ids"])
        return option_id in current_ids

    # in use
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

    # in use
    def at_id(self, email):
        return email.replace("@", "AT")

    # in use
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

    # in use
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

    # in use
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

    # in use
    def make_data_string(self, target):
        return json.dumps(target, ensure_ascii=False)

    # in use
    def make_val_string(self, target):
        return str(target)

    # in use
    def get_dict(self, target):
        try:
            return json.loads(target)
        except (json.JSONDecodeError, TypeError):
            print('current convert data to dict ')
            return target

    # in use
    def get_today(self):
        return datetime.now().strftime("%d-%m-%Y")

    # appwrite --------------------------------------------------------------------------------

    def get_all_public_saves(self, ip_data=None):

        key = None
        current_millis = self.get_millis()
        ip_control_col_name = "mam_not_logged_in_ip_control"
        public_saves_reload_time = os.getenv(
            "all_public_saves_waiting_reload_time")
        calls_in_error = int(os.getenv("calls_in_error"))

        return_saves = False

        if ip_data is None:
            return "No Id provided"

        ip_data["key"] = ip_data.get("key", self.encode_data({
            "last_update": current_millis,
            "calls_in_error": 0,
            "ipAddress": ip_data["ipAddress"]
        }))

        decoded_key = self.decode_data(ip_data["key"])
        get_ip_data = self.get_document(
            ip_control_col_name, ip_data["ipAddress"], "get_all_public_saves 01")

        # print(f"get_ip_data {get_ip_data}")

        if not get_ip_data:

            for attempt in range(5):
                new_doc = self.create_document(ip_control_col_name, ip_data["ipAddress"], {
                    "data": ip_data["key"]})
                # print(f"new_doc {new_doc}")

                if "created" in new_doc:
                    return_saves = True
                    break

        else:
            get_ip_data = get_ip_data[0]
            decoded_key = self.decode_data(get_ip_data)
            # print(f"\n\ngot doc {get_ip_data}")
            # print(f"\n\ndecoded doc {decoded_key}")

            # {'last_update': 1742694620319, 'calls_in_error': 0,'ipAddress': '201.247.15.177'}

            can_procces_new_request = self.minutes_after_last_update(
                # public_saves_reload_time
                decoded_key["last_update"], current_millis, public_saves_reload_time)

            # print(f"\n\ncan_procces_new_request {can_procces_new_request}\n\n")

            # return based on time
            if not can_procces_new_request:
                decoded_key["calls_in_error"] = int(
                    decoded_key["calls_in_error"]) + 1

                # pprint(decoded_key)

                # pprint(decoded_key)
                if decoded_key["calls_in_error"] > calls_in_error:
                    return "No new updates id 333"

                for attempt in range(5):
                    update = self.update_document(
                        ip_control_col_name,
                        ip_data["ipAddress"],
                        {"data": self.encode_data(decoded_key)}

                    )
                    # print(f"update 01 --->  {update}")
                    return_saves = True

                    if "created" in update:
                        return "please wait 5 min untill the next update id T1 "

                return "Reload your webpage"

            else:
                for attempt in range(5):
                    # reset login data
                    decoded_key["last_update"] = current_millis
                    decoded_key["calls_in_error"] = 0

                    update = self.update_document(
                        ip_control_col_name,
                        ip_data["ipAddress"],
                        {"data": self.encode_data(decoded_key)}

                    )
                    # print(f"update 02 --->  {update}")
                    if "created" in update:
                        return_saves = True
                        break

            if decoded_key["ipAddress"] != ip_data["ipAddress"]:
                decoded_key["calls_in_error"] = int(
                    decoded_key["calls_in_error"]) + 1

                if decoded_key["calls_in_error"] > calls_in_error:
                    return "please reload your webpage id R1"

        if return_saves:

            collection = "mam_public_all"
            documents = []
            limit = int(os.getenv("max_doc_len"))  # Max limit per request
            offset = 0

            while True:
                try:
                    response = self.databases.list_documents(
                        self.db_id,
                        collection,
                        queries=[Query.limit(limit), Query.offset(offset)]
                    )

                    # Extract and parse "data" field
                    for doc in response["documents"]:
                        try:
                            # Convert string to JSON
                            parsed_data = self.get_dict(doc["data"])
                            documents.append(parsed_data)
                        except json.JSONDecodeError:
                            print(
                                f"Error 305953159 Skipping invalid JSON in document {doc['$id']}")

                    # Stop when we receive fewer than `limit` docs (means no more left)
                    if len(response["documents"]) < limit:
                        break

                    offset += limit  # Move to the next batch

                except Exception as e:
                    print("Error 398263413 fetching documents:", str(e))
                    break

            print(
                f"Fetched {len(documents)} documents and saved to documents.json\n\n\n")

            documents.insert(0, {"key": ip_data["key"]})
            # pprint(self.decode_data(ip_data["key"]))
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
        print(
            f"\nget_document CCC: \n\tcollection {collection} \n\tdocument_id {document_id} \n\t{'by' if by is not None else ''} {by if by is not None else ''}\n\n"
        )

        try:
            result = self.tables_db.get_row(
                database_id=self.db_id,
                table_id=collection,
                row_id=document_id
            )

            # pprint(result)

            # Ensure 'data' exists and is not empty before parsing
            if "data" in result and result["data"]:
                try:

                    # data = result["data"]
                    parsed_data = self.get_dict(result["data"])
                    # parsed_data = parsed_data if isinstance(
                    #     parsed_data, dict) else {}

                except json.JSONDecodeError as e:
                    print(f"got error {e}")
                    parsed_data = {}

                # print("returning parsed data")

                return [
                    parsed_data,
                    result.get("today", "X"),  # 1
                    result.get("counter", "X"),  # 2
                    result.get("last_update", "X"),  # 3
                    result.get("ids", "X"),  # 4
                    result.get("indexes", "X"),  # 5
                    result.get("last_update_date", "X"),  # 6
                    result.get("bolts", "X"),  # 7
                    result.get("history", "X"),  # 8
                ]

            else:
                print("returing result")
                return result
        except AppwriteException as e:
            if "Document with the requested ID could not be found" in str(e):
                return False
            else:
                print(str(e))
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
    # apiFootball ------------------------------------------------------------------------------------------------

    # in used
    def get_match_lineup(self, fixture_id, token=None):

        if token is not None:
            account_exists = self.account_exists(token)

            if not isinstance(account_exists, bool):
                return account_exists

        else:
            return "please create an account to access this feature"

        current_line_up = self.get_document(
            "manager_line_ups", str(fixture_id), "getting match line up")

        # print(current_line_up[0])

        if not current_line_up:
            url = f"https://v3.football.api-sports.io/fixtures/lineups"

            headers = {"x-apisports-key": self.football_api_key}

            # Prepare the query parameters
            params = {"fixture": fixture_id}

            # Send the request
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                lineup_data = response.json()

                # Extract and display lineups
                if "response" in lineup_data and len(lineup_data["response"]) > 0:
                    line_up = response.json()

                    for attempt in range(5):
                        new_line_up = self.create_document("manager_line_ups", f"{fixture_id}", {
                            "data": self.make_data_string(line_up)})

                        if "created" in new_line_up:
                            return line_up
                        else:
                            time.sleep(0.5)
                else:
                    return ("Data will be ready 2 hours before the game.")
            else:
                return (f"Error: {response.status_code}, {response.text}")

        else:

            return self.get_dict(current_line_up[0])

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

    # in used
    def get_next_round(self, league_id=2, teams_len=20):

        print(f"getting next round games for {league_id} and len {teams_len}")
        if "NR" in str(league_id):
            league_id = re.sub(r"\D", "", league_id)

        print(
            f"getting next round games for second time {league_id} and len {teams_len}")

        url = f"{self.api_url}fixtures?league={league_id}&next={teams_len + (teams_len // 2)}"
        headers = {"x-apisports-key": self.football_api_key}

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
                sorted_data.insert(0, ["Friendlies", league])

            elif league["name"] == "UEFA Europa League":
                league.update({"contry_img": league["league_img"]})
                sorted_data.insert(0, ["Europa League", league])

            elif league["name"] == "UEFA Champions League":
                league.update({"contry_img": league["league_img"]})
                sorted_data.insert(0, ["Champions League", league])

        # Reorder the list
        if sorted_data:
            sorted_data.insert(2, sorted_data.pop(1))

        return sorted_data

    # in used
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
        headers = {"x-apisports-key": self.football_api_key}
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

                return data
            else:
                print("No team data found in the response.")
                return {}
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return {}

    # in used
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

        print(f"\n\nget_next_games {team_id}\nManager AI")

        if len(str(team_id)) > 10:  # if id > 10 this meand i am decodeing a jwt
            data = self.decode_data(team_id)
            league_id = data["league_id"]
            teams_len = int(data["teams_len"])
            return self.get_next_round(league_id, teams_len)

        # API details
        url = f"{self.api_url}fixtures"
        headers = {"x-apisports-key": self.football_api_key}

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

    # in used

    def update_live_game(self, data={}, id=None, testing=False, debug_mode=False):
        """Optimized version of update_live_game with better performance"""

        if debug_mode:
            print(f"\n\n---> Update_live_game ")

        # Fetch today's games only once
        to_play_games = self.get_document(
            "mam_today_games_results", "today_results", "update_live_game 01")
        to_play_games_dict = {str(self.get_data_from_dict(
            fx, "fixture,id")): fx for fx in to_play_games[0]}
        update_next_game_data = False

        # pprint(to_play_games_dict)

        if testing:
            data = {
                "future": {
                    "errors": [],
                    "get": "fixtures",
                    "paging": {"current": 1, "total": 1},
                    "parameters": {"next": "5", "team": "40"},
                    "response": [
                        {
                            "fixture": {
                                "date": "2025-01-08T20:00:00+00:00",
                                "id": 1327990,
                                "periods": {"first": None, "second": None},
                                "referee": "S. Attwell",
                                "status": {
                                    "elapsed": None,
                                    "extra": None,
                                    "long": "Not Started",
                                    "short": "NS",
                                },
                                "timestamp": 1736366400,
                                "timezone": "UTC",
                                "venue": {
                                    "city": "London",
                                    "id": 593,
                                    "name": "Test Stadium",
                                },
                            },
                        },
                    ],
                    "results": 5,
                }
            }

        future_response = data["future"]["response"]
        # num_games = len(future_response)

        # Case 1: Single or Few (<=3) games
        # if num_games <= 3:
        #     today_game = data if testing else future_response[0]
        #     today_game_id = str(get_data_from_dict(today_game, "fixture,id"))
        #     today_game_status = get_data_from_dict(
        #         today_game, "fixture,status,long")

        #     # Ignore non-live games
        #     if today_game_status in not_live_by_game_status:
        #         return data

        #     if debug_mode:
        #         print(f"today_game_id: {today_game_id}")
        #         print(
        #             f"Exists in to_play_games_ids: {today_game_id in to_play_games_dict}")

        #     # Update if exists in today's games
        #     if today_game_id in to_play_games_dict:
        #         data["future"]["response"][0] = to_play_games_dict[today_game_id]

        #     return data

        # Case 2: More than 3 games (batch update)
        for index, fixture in enumerate(future_response):

            game_id = str(fixture["fixture"]["id"])
            if game_id in to_play_games_dict:
                data["future"]["response"][index] = to_play_games_dict[game_id]
                update_next_game_data = True

        if update_next_game_data:
            pass

        return data

    # in used
    def get_ng(self, team_id=40, next_len=3, token=None):

        if token is not None:
            account_exists = self.account_exists(token)

            if not isinstance(account_exists, bool):
                return account_exists

        else:
            return "please create an account to access this feature"

        next_games_internal_id = f"next_games_team_{team_id}"
        team = None
        today = self.get_today()
        jwt_process = False

        print("\n\n--> Start getting games at get_ng MANGER AI")

        if len(str(team_id)) > 10:
            data = self.decode_data(team_id)
            nr_league_id = data["league_id"]
            current_league_id = re.sub(r"\D", "", nr_league_id)
            teams_len = int(data["teams_len"])

            print(
                f"\n\nGetting next games wit jwtToken for {current_league_id}")

            next_games_internal_id = f"next_games_team_{nr_league_id}"
            team = self.get_document(self.next_games_collection_id,
                                     next_games_internal_id, "get_ng 01")
            print(f"team gotten at get next games with jwt: \n{team}")

            if not team:
                print("not team ")
                team = [team, today, 0]
                # [False, '20-02-2025', 0]

            if today != team[1]:
                print("not today  ")
                new_request = self.get_next_round(current_league_id, teams_len)

                print(f"new_request {new_request}")
                if not len(new_request["future"]["response"]):
                    print(
                        "there is not len---------------------------------------------CC")
                    team[1] = today
                    team[0] = new_request

            # print(f"team gotten at get next games with jwt 01: \n{team}")
            jwt_process = True

        if not jwt_process:
            print("JWT was not processed ....................CC")
            team = self.get_document(self.next_games_collection_id,
                                     next_games_internal_id, "get_ng 02") if team is None else team

        print(
            f"\n\ngame gotten for today {today} {today, team[1] if team else team}")

        if not team or (today != team[1]):

            print(f"getting data from api for team id {team_id}")

            ng = self.get_next_games(team_id, next_len)
            if len(ng["future"]["response"]) == 0:
                return
            ng = self.update_live_game(ng)

            try:
                print(f"creating doc {next_games_internal_id}")
                r = self.create_document(
                    collection=self.next_games_collection_id,
                    document_id=next_games_internal_id,
                    data={
                        "data": self.make_data_string(ng),
                        "today": today,
                        "counter": 1},
                )

                if (
                    r
                    == "Document with the requested ID already exists. Try again with a different ID or use ID.unique() to generate a unique ID."
                ):
                    r = self.update_document(
                        collection=self.next_games_collection_id,
                        document_id=next_games_internal_id,
                        data={
                            "data": self.make_data_string(ng),
                            "today": today,
                            "counter": team[2] + 1,
                        },
                    )

                    if r["created"]:
                        return ng

            except AppwriteException as e:
                print(f"doc {next_games_internal_id} exists")
                if e.code == 409:  # Conflict: Document already exists
                    # Update the existing document

                    print(f"updating  doc {next_games_internal_id}")
                    r = self.update_document(
                        collection=self.next_games_collection_id,
                        document_id=next_games_internal_id,
                        data={
                            "data": self.make_data_string(ng),
                            "counter": team[2] + 1
                        },
                    )

                    if r["created"]:
                        return ng
                else:
                    raise  # Re-raise other exceptions
            return ng

        else:
            print("Getting data internally")
            ng = self.update_live_game(team[0])
            updated_doc = self.update_document(
                collection=self.next_games_collection_id,
                document_id=next_games_internal_id,
                data={
                    "data": self.make_data_string(ng),
                    "counter": team[2] + 1
                },
                by="ng with getting data internally "
            )

            print(f"updated_doc with getting data internally:  {updated_doc}")

            if "error" in updated_doc and updated_doc["error"] == 'Document not found':

                self.create_document(
                    collection=self.next_games_collection_id,
                    document_id=next_games_internal_id,
                    data={
                        "data": self.make_data_string(team[0]),
                        "today": today,
                        "counter": 1},
                )
            return ng

    # in used
    def get_tol(self, league_id=39, token=None):

        print(f"get told token {token}")

        if token is not None:
            account_exists = self.account_exists(token)

            if not isinstance(account_exists, bool):
                return account_exists

        else:
            return "please create an account to access this feature"

        league_internal_id = f"mam_league_{league_id}"
        team = self.get_document(
            self.get_teams_in_league_collection_id, league_internal_id)
        today = self.get_today()

        print(f"league_internal_id: {league_internal_id}\ntoday: {today}")

        try:
            # Check if no data or outdated data
            if not team or today != team[1]:
                tol = self.get_teams_of_league(league_id, self.season)

                # print(f"\n\n\n\n\n\n")
                # pprint(tol)
                # print(f"\n\n\n\n\n\n")

                team_ids = [str(team["team"]["id"])
                            for team in tol["response"]]
                list_team_ids = "-".join(team_ids)
                tol["team_ids"] = list_team_ids

                try:
                    # Attempt to create the document
                    cd = self.create_document(
                        collection=self.get_teams_in_league_collection_id,
                        document_id=league_internal_id,
                        data={"data": self.make_data_string(
                            tol), "today": today, "counter": 1},
                    )
                    if (
                        cd
                        == "Document with the requested ID already exists. Try again with a different ID or use ID.unique() to generate a unique ID."
                    ):
                        print("update on error ")
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
                    if e.code == 409:  # Conflict: Document already exists
                        print("01")
                        # Update the existing document
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
                        raise  # Re-raise other exceptions

                return tol
            else:

                print("getting datea internally 03")

                # pprint(team)
                data = team[0]

                team_ids = [team["team"]["id"] for team in data["response"]]
                print(f"\nteams in leage {team_ids}\n")

                idx = 0
                for id in team_ids:
                    if len(str(id)) > 5:
                        team_id_poped = data["response"].pop(idx)
                    idx += 1

                return data

        except Exception as ex:
            print(f"Error in get_tol: {ex}")
            return None

    # in used
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

        if _for == "login":
            print(f"Checking IDs... {option_id}")
            record_id = "676ae6120020af401e9e"
            while self.is_duplicate_id(option_id, mam_current_account_ids, record_id):
                option_id = "".join(random.choice(characters)
                                    for _ in range(length))

        # elif _for == "saves":
        #     print("Checking save IDs...")
        #     record_id = "all_saves_ids"
        #     while is_duplicate_id(option_id, mam_current_saves_ids, record_id):
        #         option_id = "".join(random.choice(characters) for _ in range(length))

        else:
            return option_id

        return option_id

    # in used
    def update_ids(self, col, doc, account_id_created):
        cd = self.get_document(col, doc)
        ids = self.get_dict(cd["ids"])
        ids["ids"].append(account_id_created)
        data = {"ids": self.make_data_string(ids)}
        c = self.update_document(col, doc, data)

    # in used
    def create_manager_ai_account(self, data={
            "email": "test01.jandres@gmail.com",
            "password": "password"
        }
    ):
        """

        this will return a dict

        {
            'account_id': '39F',
            'email_id': 'estebans.g.jandresATgmail.com',
            'public_key': '3LIL6LN01'
        }

        Returns:
            _type_: _description_
        """
        account_id_created = self.create_mam_id(_for="login")
        email_id = self.at_id(data["email"])

        mam_login_collection_id = self.mam_login
        mam_account_ids = "676ae5b10035cb473e22"
        mam_account_doc = "676ae6120020af401e9e"

        data_to_send = {"data": self.make_data_string({
            "password": data["password"],
            "email": data["email"],
            "account_id": account_id_created,
            "account_type": "free",
            "expiration_date": False,
            "account_freeze": False,
            "payment_history": []
        })}

        create_login = self.create_document(
            "manager_login", email_id, data_to_send)

        print("\n\n\n----------------------------------------\n\n")
        pprint(create_login)

        msg = (
            "Email allready exists"
            if create_login
            == "Document with the requested ID already exists. Try again with a different ID or use ID.unique() to generate a unique ID."
            else create_login
        )

        if isinstance(create_login, dict):
            self.update_ids(mam_account_ids, mam_account_doc,
                            account_id_created)

        return msg

    # in used
    def login_to_manager_ai_account(self, data={
            "email": "test01.jandres@gmail.com",
            "password": "password",
        }
    ):

        account = None

        account = self.get_document(
            "manager_login", self.at_id(data["email"]))

        if not account:
            return "Invalid Email address"

        account = account[0]

        # print(f"\n\n{account}\n\n")

        if account["password"] != data["password"]:
            return "Invalid Password"

        d = ["account_id", "account_type", "expiration_date",
             "account_freeze", "payment_history", "password"]
        for i in d:
            del account[i]

        return {"token": self.encode_data(account), "is_valid": True}

    def get_price_plans_and_names(self):
        managerPlanName = os.getenv("managerPlanName", "").split(",")
        managerPlanPrice = os.getenv("managerPlanPrice", "").split(",")
        managerDescriptions = os.getenv("managerDescriptions", "").split(",")

        return {
            "managerPlanName": managerPlanName,
            "managerPlanPrice": managerPlanPrice,
            "managerDescriptions": managerDescriptions

        }

    def deposit_list(self, token=None):

        if token is not None:
            account_exists = self.account_exists(token)

            if not isinstance(account_exists, bool):
                return account_exists

        else:
            return "please create an account to access this feature"

        deposit_list = os.getenv("deposit_list", "").split(",")

        # Remove any leading/trailing spaces
        deposit_list = [item.strip() for item in deposit_list]

        return (deposit_list)  # Output: ['USDT - Tron', 'BTC - Lightning']

    def get_manager_lightning_address(self, amount, token, name):

        invoice = create_invoice(amount, token, name)
        invoice["qr"] = self.gen_qr(invoice["lnInvoice"])
        return invoice

    def get_manager_usdt_tron_address(self, token):

        invoice = create_tron_wallet(token)
        invoice["qr"] = self.gen_qr(invoice["base58check_address"])
        return invoice

    def get_manager_usdt_balance(self, address, token):

        account_exists = self.account_exists(token)
        if not isinstance(account_exists, bool) or account_exists is not True:
            return account_exists

        usdt_balance = get_usdt_balance(address)
        return usdt_balance

    def get_manager_lightning_status(self, id, plan):

        status = get_invoice_by_id(id)
        if status["state"] == "PAID":
            return {
                "code": 200,
                "status": "PAID",
                "Balance": f"{status['amount']['amount']} {status['amount']['currency']}"
            }
        return {
            "code": 200,
            "status": "UNPAID"
        }

    def convert_to_milliseconds(self, timestamp, by=None):
        """
        Ensure the given timestamp is in milliseconds.
        Supports timestamps in seconds, milliseconds, 'DD-MM-YYYY', and ISO 8601 format.

        Args:
        - timestamp (int, float, or str): The timestamp to check and convert.

        Returns:
        - int: The timestamp in milliseconds.
        """

        # print(f"time stamp gotten   {timestamp} by {by}")

        # Handle ISO 8601 string format
        if isinstance(timestamp, str):
            iso_pattern = (
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$"
            )
            if re.match(iso_pattern, timestamp):
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                return int(dt.timestamp() * 1000)  # Convert to milliseconds

            # Handle 'DD-MM-YYYY' format
            try:
                dt = datetime.strptime(timestamp, "%d-%m-%Y")
                return int(dt.timestamp() * 1000)
            except ValueError:
                pass  # Continue to other checks

        # Handle numerical timestamps
        if isinstance(timestamp, (int, float, str)):

            timestamp = int(timestamp)

            # Already in milliseconds
            if timestamp >= 10**12:
                return int(timestamp)
            # Likely in seconds, convert to milliseconds
            elif timestamp < 10**10:
                return int(timestamp * 1000)

        # Raise an error for unsupported formats
        raise ValueError(
            f"Invalid timestamp format {timestamp}. Must be an int, float, or a valid date string."
        )

    def minutes_after_last_update(self, first_millis, second_millis, seconds=60):
        """
        Calculate whether a certain number of seconds have 
        passed between two timestamps in milliseconds.

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
        today_games = self.fetch_games(today, liveRequest, printRecords)
        merged_games = today_games

        indexes = {str(game["fixture"]["id"]): idx for idx,
                   game in enumerate(merged_games)}
        game_ids = list(indexes.keys())

        self.update_document(
            "mam_today_games_results",
            "today_results",
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


def get_manager_usdt_balance(address, token):
    api = Main()
    try:
        return api.get_manager_usdt_balance(address, token)
    except ValueError as e:
        return "Invalid data"


def get_manager_lightning_status(id, plan):
    api = Main()
    try:
        return api.get_manager_lightning_status(id, plan)
    except ValueError as e:
        return "Invalid id"


def today_games():
    api = Main()
    try:
        return api.today_games()
    except ValueError as e:
        return "Unable to get new games"


def create_manager_ai_account(
    data={
        "email": "test01.jandres@gmail.com",
        "password": "password"
    }
):

    api = Main()
    return api.create_manager_ai_account(data)


def login_to_manager_ai_account(
    data={
        "email": "test01.jandres@gmail.com",
        "password": "password",
    }
):

    api = Main()
    return api.login_to_manager_ai_account(data)


def get_manager_next_games(id=40, n=1, token=None):
    api = Main()
    return api.get_ng(id, n, token)


def get_manager_line_up(id=592872, token=None):
    api = Main()
    return api.get_match_lineup(id, token)


def get_manager_teams_in_league(id=39, token=None):
    api = Main()
    return api.get_tol(id, token)


def get_price_plans_and_names():
    api = Main()
    return api.get_price_plans_and_names()


# Removed incomplete function definition
def send_manager_reset_password_link(email_to, email_body, subject, replacements, my_sender):
    """

    send_email(
        recepients_body={"bcc": [], "to": ["este.g.res@gmail.com"]},
        email_body="reset_password_email",
        subject="sending from test",
        replacements={
            "emailTitle": "Your account has been created",
            "EmailBody": "Thank you for joing us "
        },
        my_sender="one"
    )

    Sends a reset password email to the specified email address.

    Args:
        email (str): The recipient's email address.
        reset_link (str): The link to reset the password.

    Returns:
        dict: A dictionary indicating the success or failure of the email sending process.
    """

    try:
        response = send_email(
            recepients_body={"bcc": [], "to": [email_to]},
            email_body=email_body,
            subject=subject,
            replacements=replacements,
            my_sender=my_sender
        )
        return response
    except Exception as e:

        return {"success": False, "message": f"Failed to send email: {str(e)}"}


def decode_token_manager_ai_token(token):

    return get_manager_ia_token_decoded(token)


def update_manager_ai_password(email, password):

    api = Main()
    current_account = api.get_document("manager_login", api.at_id(email))
    current_account = current_account[0]
    if "password" in current_account:
        current_account["password"] = password
        response = api.update_document(
            "manager_login",
            api.at_id(email),
            data={"data": api.make_data_string(current_account)},
        )

    return response


def get_manager_deposit_crypto_list(token):

    api = Main()
    return api.deposit_list(token)


def get_manager_lightning_address(amount, token, name):

    api = Main()
    return api.get_manager_lightning_address(amount, token, name)


def get_manager_usdt_tron_address(token):

    api = Main()
    return api.get_manager_usdt_tron_address(token)


def manager_decode_data(token):
    api = Main()
    return api.decode_data(token)


if __name__ == "__main__":
    pass

    today_games()
