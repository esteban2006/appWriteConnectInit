# from encodings.punycode import T
# from turtle import update
# from winreg import OpenKey


from typing import Optional, Dict, Any
from base64 import encode
from plistlib import load
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError
from jwt.exceptions import InvalidKeyError


import re
import json
import random
import string
import sys
import time
import jwt
import os
import io
import requests


from pprint import pprint
from pprint import pformat
from datetime import datetime, timedelta, timezone
from appwrite.services.tables_db import TablesDB
from appwrite.client import Client
from appwrite.services.databases import Databases  # Import the Databases class
from appwrite.services.account import Account
from appwrite.exception import AppwriteException
from appwrite.id import ID
from appwrite.query import Query

env_loaded = os.getenv("tron_api_one")


if os.getenv("secret_jwt") is None:
    env_file_path = '.env'

    with open(env_file_path, 'r') as file:
        for line in file:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# NOW read it
env_loaded = os.getenv("tron_api_one")


def common_load_tables(target="tables"):
    # env vars ----------------

    client = Client()
    client.set_endpoint(os.getenv("appwrite_end_point"))  # Your API Endpoint
    client.set_project(os.getenv("project_name"))  # Your project ID
    client.set_key(os.getenv("app_key"))  # Your secret API key
    databases = Databases(client)
    tables_db = TablesDB(client)

    if target == "tables":
        return tables_db
    if target == "databases":
        return databases


def common_dict_str(target):
    return json.dumps(target, ensure_ascii=False)


def common_str_dict(target):
    try:
        return json.loads(target)
    except (json.JSONDecodeError, TypeError):
        return target


def common_convert_to_milliseconds(timestamp, by=None):
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


def common_minutes_after_last_update(first_millis, second_millis, seconds=60):
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
        common_convert_to_milliseconds(
            first_millis, "common_minutes_after_last_update 01")
    )
    second_millis = int(
        common_convert_to_milliseconds(
            second_millis, "common_minutes_after_last_update 02")
    )

    # Calculate the difference in milliseconds
    milliseconds_difference = second_millis - first_millis

    # Convert the difference to seconds
    seconds_passed = milliseconds_difference / 1000

    # Print debug information
    print(f"\nSeconds passed: {seconds_passed:.2f}")

    # Check if the difference exceeds the threshold
    return int(seconds_passed) >= int(seconds)


def common_get_millis():
    """
    Get the current time in milliseconds since the Unix epoch.

    Returns:
    - int: Current time in milliseconds.
    """
    return int(time.time() * 1000)


def common_millis_to_datetime(millis):
    """
    Convert a Unix timestamp in milliseconds to a human-readable local date and time.
    If the input is invalid, returns a fallback date string instead of crashing.

    Args:
        millis: Expected to be an int, float, or string representing milliseconds.

    Returns:
        str: Formatted date and time (e.g., "2023-11-14 18:13:20"),
            or "Invalid date" if conversion fails.
    """
    try:
        # Ensure it's an integer (accepts int, float, or numeric string)
        millis_int = int(millis)
        seconds = millis_int / 1000.0
        dt = datetime.fromtimestamp(seconds)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError, OverflowError):
        # Return a safe fallback instead of crashing
        return "Invalid date"


def common_encode_internal(data_to_encrypt):

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


def common_decode_internal(encoded):

    if not encoded:
        return None

    keys_to_try = []

    env_key = os.getenv("secret_jwt")
    if env_key:
        keys_to_try.append(env_key)

    # fallback key
    keys_to_try.append("account_at_999")

    for key in keys_to_try:
        try:
            return jwt.decode(encoded, key, algorithms=["HS256"])
        except (DecodeError, ExpiredSignatureError, InvalidTokenError):
            continue  # try next key

    return None


def common_at_id(email):
    return email.replace("@", "AT")


def common_create_record(table_name="picker", data=None, row_id=None):
    """
    Creates a record in Appwrite Tables.

    picker table data:
        {
            email,
            text,
            status: new | viewed,
            millis
        }

    picker_accounts table data:
        {
            email,
            password,
            name,
            millis
        }
    """

    # print("create_record() called")
    # pprint(data)

    # -------------------------
    # Basic validation
    # -------------------------
    if data is None or not isinstance(data, dict):
        return {
            "error": True,
            "message": "Invalid data payload"
        }

    # -------------------------
    # Normalize & sanitize data
    # -------------------------
    millis = str(common_get_millis())
    data.setdefault("millis", millis)

    # Remove control keys
    data.pop("update", None)

    # -------------------------
    # Special handling for picker_accounts
    # -------------------------
    if table_name == "picker_accounts":
        required = ("email", "password", "name")
        for field in required:
            if field not in data or not data[field]:
                return {
                    "error": True,
                    "message": f"Missing required field: {field}"
                }

        # Generate deterministic row ID
        row_id = common_at_id(data["email"])

        # Encode sensitive fields
        data["email"] = common_encode_internal({"email": data["email"]})
        data["password"] = common_encode_internal(
            {"password": data["password"]})
        data["name"] = common_encode_internal({"name": data["name"]})

    # -------------------------
    # Special handling for picker
    # -------------------------
    if table_name == "picker":
        required = ("email", "text", "status")
        for field in required:
            if field not in data:
                return {
                    "error": True,
                    "message": f"Missing required field: {field}"
                }

    # -------------------------
    # Create document
    # -------------------------

    MAX_RETRIES = 5
    RETRY_DELAY = 0.5  # seconds (small delay to avoid hammering Appwrite)

    db_id = os.getenv("db_id")
    _tables = common_load_tables("tables")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            document_id = row_id or str(ID.unique())

            created_record = _tables.create_row(
                database_id=db_id,
                table_id=table_name,
                row_id=document_id,
                data=data
            )

            # print(
            #     f"Record created on attempt {attempt}:, {pformat(created_record)}")

            return {
                "created": True,
                # "id": document_id,
                "attempts": attempt
            }

        except AppwriteException as e:
            print(f"Attempt {attempt} failed: {e.message}")

            # Last attempt → return error
            if attempt == MAX_RETRIES:
                return {
                    "error": True,
                    "message": e.message,
                    "attempts": attempt
                }

            # Small backoff before retrying
            time.sleep(RETRY_DELAY)


def common_get_record(
    table_id: str = "data_env",
    row_id: str = "wompi_tlovendo"
) -> Optional[Dict[str, Any]]:

    print(f"[common_get_record] Fetching: table={table_id}, row={row_id}")

    try:
        db_id = os.getenv("db_id")
        endpoint = os.getenv("appwrite_end_point")
        project = os.getenv("project_name")
        key = os.getenv("app_key")

        if not all([db_id, endpoint, project, key]):
            print("[ERROR] One or more Environment Variables are missing (db_id, endpoint, project, or app_key)")
            return None

        client = Client()
        client.set_endpoint(endpoint)
        client.set_project(project)
        client.set_key(key)

        databases = Databases(client)

        # Fetch the document
        result = databases.get_document(
            database_id=db_id,
            collection_id=table_id,
            document_id=row_id
        )

        if result:
            # CRITICAL FIX: 
            # Appwrite SDK returns a 'Document' object, not a dict.
            # Converting it to dict() allows the rest of your code to use .get()
            return dict(result)
        
        return None

    except AppwriteException as e:
        # Document not found is a common "error" we want to handle gracefully
        if e.code == 404:
            print(f"[common_get_record] Document {row_id} not found in {table_id}")
        else:
            print(f"[Appwrite ERROR] {e.message} (code: {e.code})")
        return None

    except Exception as e:
        print(f"[GENERAL ERROR] in common_get_record: {str(e)}")
        return None

if __name__ == "__main__":
    pass

    # pprint(common_get_record())
    # print(common_get_millis())
    # encoded = common_encode_internal({"name": "esteban"})
    # print(encoded)
    # print(common_decode_internal(encoded))
    # create_record("picker_accounts", data={
    #               "email": "eggsteba12@gmail.com", "password": "eggsteba11@gmail.com", "name": "Esteban"})
