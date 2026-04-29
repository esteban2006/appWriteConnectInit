"""
===============================================================================
File: common_functions.py
Author: Esteban Gilberto Gutierrez Jandres
Developer: Eggsteban Jandres
Created: 2026-03-20

Description:
This module contains common utility and helper functions shared
across different parts of the application.
===============================================================================

CONFIDENTIALITY NOTICE

This file and the source code contained herein are confidential and
proprietary information belonging to Esteban Gilberto Gutierrez Jandres. The contents
of this file are intended solely for authorized use within the
associated software system.

Unauthorized access, copying, disclosure, distribution, modification,
or use of this file, in whole or in part, is strictly prohibited
without the prior written consent of the author.

AUTHORSHIP

This software module was originally designed and implemented by
Esteban Gilberto Gutierrez Jandres. Any modifications or derivative works must retain
this authorship notice unless explicitly authorized by the author.

INTELLECTUAL PROPERTY

All intellectual property rights related to the structure, design,
algorithms, and implementation contained in this file remain the
exclusive property of Esteban Gilberto Gutierrez Jandres and are protected under
applicable copyright and intellectual property laws.

USAGE RESTRICTIONS

This code is provided for use only within the intended application
environment. It may not be redistributed, sublicensed, or integrated
into other software systems without explicit written permission from
the author.

DISCLAIMER

This software is provided "as is", without warranty of any kind,
express or implied, including but not limited to warranties of
merchantability or fitness for a particular purpose.

Copyright (c) 2026 Esteban Gilberto Gutierrez Jandres
All rights reserved.
===============================================================================
"""

import base64
import hmac
import hashlib
import secrets
from base64 import encode
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
import struct

from pprint import pprint
from pprint import pformat
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from appwrite.services.tables_db import TablesDB
from appwrite.client import Client
from appwrite.services.databases import Databases  # Import the Databases class
from appwrite.services.account import Account
from appwrite.exception import AppwriteException
from appwrite.id import ID
from appwrite.query import Query

from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError
from jwt.exceptions import InvalidKeyError

if not os.getenv("appwrite_end_point"):
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

env_loading_key = "secret_jwt"
env_loaded = os.getenv(env_loading_key)
# print(f"env_loaded at common functions {type(env_loaded)}")


def commond_decode_data(encoded):
    return common_decode_dict(encoded)


def common_check_rate_limit(
    ip: str, action: str, window_seconds: int = 60
) -> tuple[bool, str]:

    table_id = os.getenv("RATE_LIMIT_COLLECTION_ID")

    print(f"\n[RATE LIMIT] Start check------------------------------")
    print(f"[RATE LIMIT] IP: {ip}, Action: {action}")

    if not table_id:
        print("[RATE LIMIT] No table configured")
        return True, "Rate limit not configured"

    try:
        safe_ip = ip.replace(":", "_").replace(".", "_")
        doc_id = f"{safe_ip}_{action}"

        now = datetime.now(timezone.utc)

        print(f"[RATE LIMIT] Doc ID: {doc_id}")

        # -----------------------------
        # 1. GET EXISTING RECORD
        # -----------------------------
        record = common_get_record(table_id, doc_id)

        if record:
            f"[RATE LIMIT] Existing record: \n{pformat(record['data'])}"

        if record:
            current_count = int(record.get("data", {}).get("count", 0))
            reset_at_str = record.get("data", {}).get("reset_at", 0)

            print(f"[RATE LIMIT] Count: {current_count}")
            print(f"[RATE LIMIT] Reset at raw: {reset_at_str}")

            try:
                reset_at = datetime.fromisoformat(reset_at_str.replace("Z", "+00:00"))
            except Exception:
                print("[RATE LIMIT] Failed to parse reset_at → forcing reset")
                reset_at = now

            max_requests = int(
                common_rate_limits_dicts()[action]
                or os.getenv("RATE_LIMIT_DEFAULT", "5")
            )

            print(f"[RATE   wed]: {max_requests}")

            # -----------------------------
            # 2. STILL IN WINDOW
            # -----------------------------
            if reset_at > now:
                print("[RATE LIMIT] Inside window")

                if current_count >= max_requests:
                    print(f"[RATE LIMIT] LIMIT EXCEEDED \n\n{'*'*80}\n\n")
                    return False, f"Limit exceeded ({int(max_requests) - 1})"

                update_result = common_update_record(
                    table_name=table_id,
                    row_id=doc_id,
                    data={"count": current_count + 1},
                )

                print(f"[RATE LIMIT] Update result: {update_result}")

                if update_result.get("error"):
                    print("[RATE LIMIT] Update FAILED")

                return True, "OK"

            # -----------------------------
            # 3. WINDOW EXPIRED → RESET
            # -----------------------------
            print("[RATE LIMIT] Window expired → resetting")

            new_reset = now + timedelta(seconds=window_seconds)

            update_result = common_update_record(
                table_name=table_id,
                row_id=doc_id,
                data={"count": 1, "reset_at": new_reset.isoformat()},
            )

            print(f"[RATE LIMIT] Reset result: {update_result}\n\n{'*'*80}")

            return True, "OK"

        # -----------------------------
        # 4. RECORD DOES NOT EXIST → CREATE
        # -----------------------------
        print("[RATE LIMIT] No record → creating new one")

        new_reset = now + timedelta(seconds=window_seconds)

        create_result = common_create_record(
            table_name=table_id,
            row_id=doc_id,
            data={
                "ip_action_key": doc_id,
                "count": 1,
                "reset_at": new_reset.isoformat(),
            },
        )

        print(f"[RATE LIMIT] Create result: {create_result}")

        if create_result.get("error"):
            print("[RATE LIMIT] CREATE FAILED")

        return True, "OK"

    except Exception as e:
        print(f"[RATE LIMIT ERROR] {str(e)}")
        import traceback

        traceback.print_exc()
        return True, "Fail-open"


def common_load_tables(target="tables"):
    """
    Returns either TablesDB or Databases service based on target.
    """
    client = Client()

    # Use Appwrite Cloud variables first, then fallback to your local names
    endpoint = os.getenv("APPWRITE_FUNCTION_ENDPOINT") or os.getenv(
        "appwrite_end_point"
    )
    project = os.getenv("APPWRITE_FUNCTION_PROJECT_ID") or os.getenv("project_name")
    api_key = os.getenv("APPWRITE_FUNCTION_API_KEY") or os.getenv("app_key")

    if not endpoint or not project:
        print("[CRITICAL] Missing Appwrite Endpoint or Project ID")

    client.set_endpoint(endpoint)
    client.set_project(project)

    if api_key:
        client.set_key(api_key)
    else:
        # This is why you get the 401 error
        print("[WARNING] No API Key found! Acting as Guest.")

    if target == "tables":
        return TablesDB(client)

    if target == "databases":
        return Databases(client)

    raise ValueError(f"Unknown target: {target}")


def common_log_debug(message: str):

    if os.getenv("print_logs"):
        print(f"[DEBUG] {common_get_millis()} {message}")


def _clean_document(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove Appwrite metadata fields ($...)"""
    return {k: v for k, v in data.items() if not k.startswith("$")}


def common_one_dict(d, priority_keys=None):
    if priority_keys is None:
        priority_keys = []

    result = {}

    def _flatten(d_dict):
        for k, v in d_dict.items():
            if isinstance(v, dict):
                _flatten(v)
            else:
                result[k] = v

    _flatten(d)

    # print("Flattened dict:", result)
    # print("Priority keys:", priority_keys)

    # Build sort key map
    priority_map = {key: idx for idx, key in enumerate(priority_keys)}

    def sort_key(item):
        key = item[0]
        if key in priority_map:
            return (0, priority_map[key])  # Keep specified order
        return (1, key)  # Alphabetical for others

    # Sort items
    sorted_items = sorted(result.items(), key=sort_key)

    # Return a regular dict with insertion order preserved (Python 3.7+)
    return dict(sorted_items)


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
            first_millis, "common_minutes_after_last_update 01"
        )
    )
    second_millis = int(
        common_convert_to_milliseconds(
            second_millis, "common_minutes_after_last_update 02"
        )
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


def common_encode_one_value(one_value):
    secret = os.getenv("secret_jwt")

    if not secret:
        raise ValueError("Missing secret_jwt environment variable")

    payload = one_value if isinstance(one_value, dict) else {"value": one_value}

    try:
        return jwt.encode(payload, secret, algorithm="HS256")
    except Exception as e:
        raise ValueError(f"JWT encoding failed: {str(e)}")


def common_decode_one_value(token):
    secret = os.getenv("secret_jwt")

    if not secret:
        raise ValueError("Missing secret_jwt environment variable")

    try:
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        return decoded

    except jwt.ExpiredSignatureError:
        return {"error": True, "message": "Token expired"}

    except jwt.InvalidTokenError:
        return {"error": True, "message": "Invalid token"}

    except Exception as e:
        return {"error": True, "message": f"Decode failed: {str(e)}"}


def common_encode_dict(data_to_encrypt):

    private_key = os.getenv("secret_jwt")

    if not private_key:
        raise ValueError("Missing PRIVATE_KEY in environment variables")

    # Ensure the input is a dictionary
    if not isinstance(data_to_encrypt, dict):
        raise TypeError("data_to_encrypt must be a dictionary")

    try:
        # Encode JWT with proper error handling
        token = jwt.encode(data_to_encrypt, private_key, algorithm="HS256")
        return token

    except InvalidKeyError:
        raise ValueError("Invalid private key. Ensure it is a valid RSA private key.")

    except TypeError as e:
        raise ValueError(f"Invalid data format: {str(e)}")

    except Exception as e:
        raise ValueError(f"An unexpected error occurred while encoding JWT: {str(e)}")


def common_decode_dict(encoded):

    """_summary_

    Returns:
        dict or none
    """

    if not encoded:
        return None

    keys_to_try = []

    env_key = os.getenv("secret_jwt")
    if env_key:
        keys_to_try.append(env_key)

    # fallback key
    # keys_to_try.append("secret_jwt2")
    # keys_to_try.append("account_at_999")

    for key in keys_to_try:
        try:
            return jwt.decode(encoded, key, algorithms=["HS256"])
        except (DecodeError, ExpiredSignatureError, InvalidTokenError):
            continue  # try next key

    return None


def common_at_id(email):
    return email.replace("@", "AT")


def common_create_record(table_name="security_db", data=None, row_id=None):

    # print("create_record() called")
    # pprint(data)

    # -------------------------
    # Basic validation
    # -------------------------
    if data is None or not isinstance(data, dict):
        return {"error": True, "message": "Invalid data payload"}

    # -------------------------
    # Normalize & sanitize data
    # -------------------------

    # Remove control keys
    data.pop("update", None)
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
                database_id=db_id, table_id=table_name, row_id=document_id, data=data
            )

            # print(
            #     f"Record created on attempt {attempt}:, {pformat(created_record)}")

            return {"created": True, "id": document_id, "attempts": attempt}

        except AppwriteException as e:
            print(f"Attempt {attempt} failed: {e.message}")
            if "already exists" in e.message:
                return {e.message}

            # Last attempt → return error
            if attempt == MAX_RETRIES:
                return {"error": True, "message": e.message, "attempts": attempt}

            # Small backoff before retrying
            time.sleep(RETRY_DELAY)


def common_update_record(table_name="security_db", row_id=None, data=None):

    # -------------------------
    # Basic validation
    # -------------------------
    if not row_id:
        return {"error": True, "message": "row_id is required"}

    if data is None or not isinstance(data, dict):
        return {"error": True, "message": "Invalid data payload"}

    # -------------------------
    # Normalize & sanitize data
    # -------------------------
    data.pop("update", None)

    # -------------------------
    # Update document
    # -------------------------
    MAX_RETRIES = 2
    RETRY_DELAY = 0.5

    db_id = os.getenv("db_id")
    _tables = common_load_tables("tables")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            updated_record = _tables.update_row(
                database_id=db_id, table_id=table_name, row_id=row_id, data=data
            )

            return {"updated": True, "id": row_id, "attempts": attempt}

        except AppwriteException as e:
            print(f"\n\n[Update Attempt {attempt}] {e.message}\n\n")

            if attempt == MAX_RETRIES:
                return {"error": True, "message": e.message, "attempts": attempt}

            time.sleep(RETRY_DELAY)


def common_get_record(table_id: str, row_id: str) -> Optional[Dict[str, Any]]:
    try:
        db_id = os.getenv("db_id")
        if not db_id:
            raise ValueError("Missing environment variable: db_id")

        tables = common_load_tables("tables")
        result = tables.get_row(database_id=db_id, table_id=table_id, row_id=row_id)

        if result:
            # 1. Appwrite SDK objects usually have a to_dict() method
            if hasattr(result, "to_dict"):
                data_dict = result.to_dict()

            # 2. If it's a Pydantic v2 model (standard in Python 3.9+ environments)
            elif hasattr(result, "model_dump"):
                data_dict = result.model_dump()

            # 3. Fallback for older Pydantic or simple objects
            elif hasattr(result, "__dict__"):
                # We use __dict__.items() instead of dir() to avoid metadata warnings
                data_dict = {
                    k: v for k, v in result.__dict__.items() if not k.startswith("_")
                }

            else:
                data_dict = dict(result)

            return _clean_document(data_dict)

        return None

    except Exception as e:
        print(f"[GENERAL ERROR] {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def common_get_all_records(table_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    try:
        db_id = os.getenv("db_id")
        if not db_id:
            raise ValueError("Missing environment variable: db_id")

        tables = common_load_tables("tables")

        offset = 0
        all_rows = []

        while True:
            response = tables.list_rows(
                database_id=db_id,
                table_id=table_id,
                queries=[Query.limit(limit), Query.offset(offset)],
            )

            rows = (
                response.get("rows", [])
                if isinstance(response, dict)
                else getattr(response, "rows", [])
            )

            if not rows:
                break

            for result in rows:

                # Normalize object → dict
                if hasattr(result, "to_dict"):
                    data_dict = result.to_dict()

                elif hasattr(result, "model_dump"):
                    data_dict = result.model_dump()

                elif hasattr(result, "__dict__"):
                    data_dict = {
                        k: v
                        for k, v in result.__dict__.items()
                        if not k.startswith("_")
                    }

                else:
                    data_dict = dict(result)

                all_rows.append(_clean_document(data_dict))

            if len(rows) < limit:
                break

            offset += limit

        return all_rows

    except Exception as e:
        print(f"Error retrieving rows: {e}")
        return []


def common_generate_id(prefix="333", id_len=40):
    return f"{prefix}_{''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(id_len))}"


def common_generate_int_id(id_len=128):
    return (
        f"{''.join(random.SystemRandom().choice(string.digits) for _ in range(id_len))}"
    )


def common_rate_limits_dicts():

    env_str = os.getenv("RATE_LIMITS")
    parts = env_str.split(",")

    if len(parts) % 2 != 0:
        raise ValueError("Invalid format: must be key,value pairs")

    return {parts[i]: int(parts[i + 1]) for i in range(0, len(parts), 2)}


def common_shift_text(text, shift):

    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits

    result = ""

    for char in text:

        if char in lower:
            i = lower.index(char)
            result += lower[(i + shift) % 26]

        elif char in upper:
            i = upper.index(char)
            result += upper[(i + shift) % 26]

        elif char in digits:
            i = digits.index(char)
            result += digits[(i + shift) % 10]

        else:
            result += char

    return result


def common_shift_text_to_int(text, shift):

    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits

    result = ""

    for char in text:

        if char in lower:
            i = lower.index(char)
            result += digits[(i + shift) % 10]

        elif char in upper:
            i = upper.index(char)
            result += digits[(i + shift) % 10]

        elif char in digits:
            i = digits.index(char)
            result += digits[(i + shift) % 10]

        else:
            result += char

    return int(result)


def common_minutes_to_future_ms(minutes: int) -> int:
    now_ms = int(time.time() * 1000)  # current time in milliseconds
    future_ms = now_ms + (minutes * 60 * 1000)
    return future_ms


def common_get_expiration(minutes: int):
    """
    Generate current and expiration timestamps.

    Args:
        minutes (int): Minutes until expiration.

    Returns:
        tuple: now_ms, exp_ms, now_sec, exp_sec
    """

    now_sec = int(time.time())
    exp_sec = now_sec + minutes * 60

    return now_sec * 1000, exp_sec * 1000, now_sec, exp_sec


def common_is_expired(timestamp: int) -> bool:
    """
    Returns True if expired, False if still valid.
    Accepts seconds or milliseconds timestamps.
    """

    now_sec = int(time.time())
    now_ms = now_sec * 1000

    if timestamp > 1_000_000_000_000:
        return now_ms > timestamp

    return now_sec > timestamp


def common_generate_jwt_payment_token(merchant_id: str = "NoUser", minutes: int = 1):

    pid = common_generate_int_id(9)
    secret = os.getenv("secret_jwt")

    now = int(time.time())
    exp = now + (minutes * 60)

    payload = {"pid": pid, "mid": merchant_id, "iat": now, "exp": exp}

    return {"token": jwt.encode(payload, secret, algorithm="HS256"), "pid": pid}


def common_decode_payment_token(token):
    secret = os.getenv("secret_jwt")

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload

    except jwt.ExpiredSignatureError:
        return {"error": "link expired"}

    except jwt.InvalidTokenError:
        return {"error": "invalid link"}


BASE62 = string.digits + string.ascii_letters
BASE62_MAP = {c: i for i, c in enumerate(BASE62)}


def base62_encode(num):

    if num == 0:
        return BASE62[0]

    arr = []
    base = 62

    while num:
        num, rem = divmod(num, base)
        arr.append(BASE62[rem])

    return "".join(reversed(arr))


def base62_decode(s):
    num = 0

    for char in s:
        num = num * 62 + BASE62_MAP[char]

    return num


def common_generate_payment_token(minutes=5):

    pid = secrets.randbits(32)
    secret = os.getenv("secret_jwt")
    exp = int(time.time()) + minutes * 60

    raw = pid.to_bytes(4, "big") + exp.to_bytes(4, "big")

    sig = hashlib.sha256(raw + secret.encode()).digest()[:4]

    token_bytes = raw + sig

    num = int.from_bytes(token_bytes, "big")

    return {"token": base62_encode(num), "pid": pid, "exp": exp}


def common_verify_payment_token(token):

    if token is None:
        return {"pid": secrets.randbits(32), "token": True, "code": 201}

    secret = os.getenv("secret_jwt")

    try:
        num = base62_decode(token)

        data = num.to_bytes(12, "big")

        raw = data[:8]
        sig = data[8:]

        expected = hashlib.sha256(raw + secret.encode()).digest()[:4]

        if sig != expected:
            return {"msg": "Invalid token", "code": 500}

        pid = int.from_bytes(raw[:4], "big")
        exp = int.from_bytes(raw[4:], "big")

        if time.time() > exp:
            pid = secrets.randbits(32)
            return {"msg": "Invalid token - exp", "code": 202}

        return {"pid": pid, "exp": exp, "token": True, "code": 200}

    except:
        pid = secrets.randbits(32)
        return {"msg": "Something went wrong", "code": 203}


def send_email(
    _from: str = "tlovendo",
    to: str = "",
    subject: str = "email_verification",
    lang: str = "en",
    data: dict = None,
    test: bool = True,
):
    # 1. Import Common Functions
    try:
        from .email_service.send_email_btc import sendEmailBtc

    except (ImportError, ValueError):
        from email_service.send_email_btc import sendEmailBtc

    sendEmailBtc(_from, to, subject, lang, data, test)


# TOTP GENERATION


def common_generate_2fa_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8")


def common_generate_totp(secret, digits=6, interval=30):
    key = base64.b32decode(secret)

    counter = int(time.time() // interval)

    msg = struct.pack(">Q", counter)

    h = hmac.new(key, msg, hashlib.sha1).digest()

    offset = h[-1] & 0x0F

    binary = struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF

    otp = binary % (10**digits)

    return str(otp).zfill(digits)


def common_verify_totp(secret, user_code):

    for offset in [-1, 0, 1]:  # allow 30 sec clock drift
        counter = int(time.time() // 30) + offset

        key = base64.b32decode(secret)
        msg = struct.pack(">Q", counter)

        h = hmac.new(key, msg, hashlib.sha1).digest()
        o = h[-1] & 0x0F
        binary = struct.unpack(">I", h[o : o + 4])[0] & 0x7FFFFFFF

        otp = str(binary % (10**6)).zfill(6)

        if otp == user_code:
            return True

    return False


# USER DATA


def common_create_avatar(firstName=None, lastName=None):

    if firstName is None or lastName is None:
        return ""
    return f"https://ui-avatars.com/api/?name={firstName}+{lastName}&background=139024&color=fff&bold=true&rounded=true&format=svg"


def common_get_mam_user_data():
    """
    Returns the default user data structure used in the MAM system.

    This function provides a standardized dictionary template for creating
    or initializing a user record. All fields are initialized with empty
    values and are intended to be populated when a user account is created
    or updated.

    Returns
    -------
    dict
        Dictionary containing the default user schema.

    Fields
    ------
    account_id : str
        Unique identifier for the user account (typically the email).

    account_type : str
        Account tier of the user (e.g., basic, silver, gold, premium).

    account_verified : str
        Indicates whether the user account has been verified.

    avatar : str
        URL of the user's avatar image.

    balance : str
        Current user balance.

    balance_history : str
        Historical balance changes.

    created_at : str
        Timestamp of when the account was created.

    deposits : str
        JSON string representing deposit history.
        Example: '{"pendings": [], "approved": []}'.

    email : str
        User email address.

    fav_teams : str
        List or serialized data of user's favorite teams.

    first_name : str
        User's first name.

    has_code : str
        Indicates whether the user has enabled TOTP authentication.

    language : str
        User's preferred language.

    last_name : str
        User's last name.

    last_store_update : str
        Timestamp of the last store update related to the user.

    last_store_update_counter : str
        Counter tracking the number of store updates.

    marketing_accepted : str
        Indicates if the user has accepted marketing communications.

    password : str
        User password (should be stored hashed).

    profile : str
        Profile metadata or serialized user profile information.

    public_key : str
        Public key used for TOTP authentication.

    referred_by : str
        Referral identifier of the user who referred this account.

    referral_id : str
        Unique 6-digit referral code assigned to the user.

    role : str
        Role assigned to the user (e.g., client, admin).

    saves : str
        Saved user data or preferences.

    tax : str
        Tax-related information for the user.

    uid : str
        Unique 40-character mixed identifier for the user.

    user_name : str
        Username displayed for the user.

    verification_email_sent_count : str
        Number of verification emails sent to the user.
    """
    return {
        "account_id": "",  # their email address
        "account_type": "",  # basic, silver, gold, premium
        "account_verified": "",
        "avatar": "",  # https://ui-avatars.com/api/?name=${firstName}+${lastName}&background=F2C94C&color=fff&bold=true&rounded=true&format=svg
        "balance": "",
        "balance_history": "",
        "created_at": "",
        "deposits": "",  #'{"pendings": [], "approved": []}',
        "email": "",
        "fav_teams": "",
        "first_name": "",
        "has_code": "",  # totp
        "language": "",  # users prefered language
        "last_name": "",
        "last_store_update": "",
        "last_store_update_counter": "",
        "marketing_accepted": "",
        "password": "",
        "profile": "",
        "public_key": "",  # totp key
        "referred_by": "",
        "referral_id": "",  # 6 digits int
        "role": "",  # client, admin
        "saves": "",
        "tax": "",
        "uid": "",  # 40 digits mix
        "user_name": "",
        "verification_email_sent_count": "",
    }


def common_create_test_gemini_table(
    table_id="mam_users",
    name="mam_users",
    keys=[
        "account_id",
        "account_verified",
        "avatar",
        "balance",
        "balance_history",
        "busines_tax",
        "created_at",
        "deposits",
        "email",
        "fav_teams",
        "first_name",
        "has_code",
        "language",
        "last_name",
        "last_store_update",
        "last_store_update_counter",
        "marketing_accepted",
        "password",
        "profile",
        "public_key",
        "referred_by",
        "referral_id",
        "role",
        "saves",
        "tax",
        "uid",
        "user_name",
        "verification_email_sent_count",
    ],
):

    tables_db = common_load_tables()

    # Map every key to a 'string' type with a large size (acting like longtext)
    # 16383 is the maximum size for a standard indexed string/varchar in many DBs
    columns = []
    for key in keys:
        columns.append(
            {
                "key": key,
                "type": "string",  # Using 'string' as the universal type
                "size": 16383,  # Large size to handle long text
                "required": False,
            }
        )

    try:
        result = tables_db.create_table(
            database_id="66d68aff00057628676d",
            table_id=table_id,
            name=name,
            columns=columns,
            indexes=[],  # No indexes to ensure creation success for large strings
        )
        print("Success! Table created using 'string' types.")
        return result
    except Exception as e:
        print(f"Error creating table: {e}")
    except Exception as e:
        print("Error creating table:", str(e))


def ms_from_config(cfg):
    if not cfg:
        return 0

    if "seconds" in cfg:
        return cfg["seconds"] * 1000

    if "minutes" in cfg:
        return cfg["minutes"] * 60 * 1000

    if "hours" in cfg:
        return cfg["hours"] * 60 * 60 * 1000

    if "days" in cfg:
        return cfg["days"] * 24 * 60 * 60 * 1000

    return 0


def common_time_passed(last_timestamp_ms: int, cfg: dict) -> bool:
    """
    Check whether a specified time interval has passed since a given timestamp.

    The function compares the current time with a previous timestamp and
    determines if the configured interval has elapsed.

    Example:
        if common_time_passed(last_run, {"hours": 1}):
            print("Run hourly task")

    Args:
        last_timestamp_ms (int):
            The previous timestamp in milliseconds.

        cfg (dict):
            Configuration dictionary defining the time interval.
            Supported keys:
                - "seconds"
                - "minutes"
                - "hours"
                - "days"

            Example:
                {"minutes": 5}

    Returns:
        bool:
            True if the configured time interval has passed since
            `last_timestamp_ms`, otherwise False.
    """
    now = int(time.time() * 1000)
    interval = ms_from_config(cfg)

    if not interval:
        return False

    return (now - last_timestamp_ms) >= interval


def common_ensure_millis(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return False

    now = int(time.time() * 1000)
    year_2000 = 946684800000

    if year_2000 <= value <= now:
        return True

    return False


if __name__ == "__main__":

    pass
    create_record_data = {
        "success": True,
        "data": {
            "token": "wKopPiUxa0CzfBX+Km3aMg==",
            "tarjetaEnmascarada": "5230 4506 XXXX 8871 ",
        },
        "message": "Card tokenized successfully",
        "config_id": "tlovendo",
    }
    create_record_data = {
        "ip_action_key": "123456789",
        "count": 4,
        "reset_at": "2026-03-19T06:32:25.100+00:00",
    }
    row_id = "test_one_02"

    print (common_decode_dict("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6ImV5SmhiR2NpT2lKSVV6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUoxYVdRaU9pSXhjM2xMUnpsd1ZIQlpNVlZvVFZKclRTSjkuemlyZlVrVnpOMjhRdHJ2dl9hTHMzWGg2T1Racnc1SU9ZN1IwUzhIdldLayIsImVtYWlsIjoiZXN0ZWJhbkBnbWFpbC5jb20iLCJleHAiOjE3Nzc0OTI2NDR9.LB0OVxHsy4cMMld9mUbrmqXdHilrMHdqu-s_IbngtNs"))
    # print(common_generate_int_id(8))

    # pprint(common_get_all_records("mam_public_saves"))

    # print(common_create_avatar("esteban", "jandres"))
    # common_create_test_gemini_table()

    # print(generate_2fa_secret())
    # topt = "CDXWW7QG3ZKFCM42NGUBRUWSTLK6MCAO"
    # totp_generation = common_generate_totp(topt)
    # print(totp_generation)
    # print(common_verify_totp(topt, totp_generation))

    # send_email(
    #     _from="tlovendo",
    #     to="esteban.g.jandres@gmail.com",
    #     subject="email_order",
    #     lang="es",
    #     data={
    #         "app_name": "tlovendo",
    #         "name": "Esteban Jandres",
    #         "expiration_minutes": 5,
    #         "theme": "#ff8f9c",
    #         "order_id": common_generate_int_id(6),
    #     },
    #     test=True,
    # )
    # print(common_generate_int_id())

    # l = common_generate_payment_token(minutes=1)

    # print("ID:", l)
    # print("Timestamp:", common_verify_payment_token(l["token"]))

    # print(base62_encode(common_shift_text_to_int(
    #     "gtmS7cFpWhWB2LFFxZ82Dze3tZD3", 3)))

    # print(common_minutes_to_future_ms(5))
    # one, two, three = common_get_expiration(5)

    # print("Created:", one)
    # print("Expires:", two)
    # print("Expires three:", three)

    # id = (common_generate_int_id(9))
    # print(id)
    # encode = common_shift_text("1845-creaditcard", id)
    # print(encode)
    # print(common_shift_text(encode, -id))

    # pprint(common_rate_limits_dicts())

    # pprint(common_decode_dict("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBJZCI6ImZkY2RjNDNmLTkxMGQtNGM3Ni04YWFjLTVlNjNjYTkyMmVkYyIsImFwcFNlY3JldCI6ImQzYzg4OWIyLTQ0ZGQtNGJkMy04ZjUzLTZkZmYzMjcxMzQzMiJ9.-rLISnRjNMhiLOoqIMA5R280sVP30r95QTFBQs-_g50"))

    # print(common_encode_dict({
    #     "appId": "fdcdc43f-910d-4c76-8aac-5e63ca922edc",
    #     "appSecret": "d3c889b2-44dd-4bd3-8f53-6dff32713432"
    # }))
    # t = (common_encode_one_value("esteban"))
    # print(t)
    # print(common_decode_one_value(t))
    # pprint(common_update_record(table_name="security_db",
    #        data=create_record_data, row_id=row_id))
    # pprint(common_create_record("security_db", create_record_data, row_id=row_id))

    # record = common_get_record(
    #     os.getenv("get_teams_in_league_collection_id"),
    #     f"mam_league_10",
    # )
    # pprint(record)

    # response_data = record["data"]["data"]
    # first_decode = json.loads(response_data)
    # print(first_decode)
    # rr = common_get_record("email_server_data", "payNus")
    # print(f"\n\nrecord gotten \n{pformat(common_decode_dict(rr["data"]["data"]))}")

    # print(common_load_tables())
    # print(common_generate_id())
    # print(common_get_millis())
    # encoded = (common_encode_dict({
    #     "appId": "fdcdc43f-910d-4c76-8aac-5e63ca922edc",
    #     "appSecret": "d3c889b2-44dd-4bd3-8f53-6dff32713432"
    # }))
    # print(encoded)
    # print(common_decode_dict(encoded))
    # create_record("picker_accounts", data={
    #               "email": "eggsteba12@gmail.com", "password": "eggsteba11@gmail.com", "name": "Esteban"})
