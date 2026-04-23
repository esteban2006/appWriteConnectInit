# from encodings.punycode import T
# from turtle import update
# from winreg import OpenKey


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


from typing import Optional, Dict, List


# files to be imported
from common_functions import *

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


# manual process -------------

class Main:

    """




    Account data
    {
        'account_type': 4,
        'status': 'paid',
        'targets': '1',  ---> keep in mind that 0 counts as 1
        'targets_allowed': 5,
        'telegram_data': []
    }



    account types :
        individual: 1 = 1 target
        familiar: 2 = 5 targets
        individual_premium = 3 = 1 with telegram
        familiar_premium = 4 = 5 with telegram
        extra_device = 5 + 1
        pay_as_you_go = 6 = 0.01
        device_lifet_ime = 7 = 1000


    jwt
        {
            'email': 'eggsteba10@gmail.com', 
            'millis': 1768754431284, 
            'status': 'created'
        }


    accounts status can:
        created
        paid
        not paid : within 10 days after payment (late payyment )
        finished :  client decied to cancel the service


    telegram_status

    notice that device id 0 will be the first id

        {
            chcommon_at_id : fdsa
            token : asfd
            device_id : 0
            send: yes / no
            linked : eggsteban@gmail.com
        }


    when saving data on family pack We need to add "_1" 
    right before the @ sign so we could i dentify the device idx



    """

    def __init__(self):

        self.start_timestamp_ = None

        # env vars ----------------
        self.printer = os.getenv("PRINTER")
        self.db_id = os.getenv("db_id")
        self.databases = common_load_tables("databases")
        self.tables_db = common_load_tables("tables")

        # --------------------------------------------------
        # importan variables to share
        # --------------------------------------------------
        self.login_session_in_seconds = os.getenv(
            "picker_login_session_in_seconds")

    def recover_email(self, obfuscated_email: str) -> str:
        """
        Recover a real email address from an obfuscated string.

        Supported patterns:
        - Removes `_id_<number>`
        - Converts `_@`, `_AT`, `AT` to `@`

        Examples:
            eggsteban_id_1_@gmail.com -> eggsteban@gmail.com
            eggsteban_id_2_ATgmail.com -> eggsteban@gmail.com
        """
        if not obfuscated_email:
            return ""

        email = obfuscated_email

        # Remove `_id_<number>`
        email = re.sub(r"_id_\d+", "", email)

        # Normalize separators to '@'
        # email = re.sub(r"(_@|_AT|AT)", "@", email)

        # Clean up accidental double symbols
        email = re.sub(r"_+", "", email)

        return email

    def extract_email_id(self, email: str) -> Optional[int]:
        """
        Extract the numeric ID from an obfuscated email.

        Expected pattern:
            *_id_<number>_@*

        Example:
            eggsteban_id_1_@gmail.com -> 1

        Returns:
            int if found, otherwise None
        """
        if not email:
            return None

        match = re.search(r"_id_(\d+)_@", email)
        if not match:
            return 0

        return int(match.group(1))

    def get_pendings_with_fallback_and_update(self, token):

        decoded_token = common_decode_internal(token)
        email = decoded_token["email"]
        status = decoded_token["status"]
        millis = decoded_token["millis"]
        current_millis = common_get_millis()

        print(f"decoded token {decoded_token}")

        if common_convert_to_milliseconds(millis, current_millis, self.login_session_in_seconds):
            return {
                "error": True,
                "message": "login expired, please login again",
                "code": "0x0001"
            }

        # decoded token
        # {
        #     'email': 'email@gmail.com',
        #     'millis': 1769211689215,
        #     'status': 'created'
        # }

        if status != "paid":
            return {
                "message": "Please get a subscription to start getting your messages ",
                "code": "501"
            }

        MAX_TOTAL = 100
        PAGE_SIZE = 100

        all_pendings = []
        last_cursor = None

        # 1️⃣ Traer TODOS los pendings
        while True:
            queries = [
                Query.equal("email", email),
                Query.equal("status", "new"),
                Query.order_desc("$createdAt"),
                Query.limit(PAGE_SIZE)
            ]

            if last_cursor:
                queries.append(Query.cursor_after(last_cursor))

            result = self.tables_db.list_rows(
                database_id=self.db_id,
                table_id="picker",
                queries=queries
            )

            rows = result["rows"]

            if not rows:
                break

            all_pendings.extend(rows)

            if len(rows) < PAGE_SIZE:
                break

            last_cursor = rows[-1]["$id"]

        # 2️⃣ Si hay más de 100 pendings → solo usar los primeros 100
        pendings_to_return = all_pendings[:MAX_TOTAL]

        # 3️⃣ Si faltan, completar con DONE
        if len(pendings_to_return) < MAX_TOTAL:
            remaining = MAX_TOTAL - len(pendings_to_return)

            done_result = self.tables_db.list_rows(
                database_id=self.db_id,
                table_id="picker",
                queries=[
                    Query.equal("email", email),
                    Query.equal("status", "done"),
                    Query.order_desc("$createdAt"),
                    Query.limit(remaining)
                ]
            )

            done_rows = done_result["rows"]
        else:
            done_rows = []

        # 4️⃣ 🔥 ACTUALIZAR STATUS de los pendings devueltos
        for row in pendings_to_return:
            self.tables_db.update_row(
                database_id=self.db_id,
                table_id="picker",
                row_id=row["$id"],
                data={
                    "status": "viewed"  # o "done"
                }
            )

            # Reflejar el cambio también en memoria
            row["status"] = "viewed"

        # 5️⃣ Retornar resultado final

        final_rows = pendings_to_return + done_rows

        # remove Appwrite system keys
        final_rows = [
            {k: v for k, v in row.items() if not k.startswith("$")}
            for row in final_rows
        ]

        return final_rows

    def get_new_messages_range(self, email, from_idx=0, to_idx=100):
        """
        Fetch NEW messages in a range using Appwrite cursor pagination.

        Examples:
            from_idx=0,   to_idx=100   -> last 100
            from_idx=100, to_idx=200   -> messages 100-200
        """

        if from_idx < 0 or to_idx <= from_idx:
            raise ValueError("Invalid range")

        PAGE_SIZE = 100
        all_rows = []
        last_cursor = None
        fetched = 0

        while fetched < to_idx:
            queries = [
                Query.equal("email", email),
                # Query.equal("status", "new"),
                Query.order_desc("$createdAt"),
                Query.limit(PAGE_SIZE)
            ]

            if last_cursor:
                queries.append(Query.cursor_after(last_cursor))

            result = self.tables_db.list_rows(
                database_id=self.db_id,
                table_id="picker",
                queries=queries
            )

            print(result)

            rows = result["rows"]
            if not rows:
                break

            all_rows.extend(rows)
            fetched += len(rows)
            last_cursor = rows[-1]["$id"]

            if len(rows) < PAGE_SIZE:
                break

        # Slice the requested window
        selected = all_rows[from_idx:to_idx]

        # Remove Appwrite system keys
        return [
            {k: v for k, v in row.items() if not k.startswith("$")}
            for row in selected
        ]

    def get_account(self, email):

        email = common_encode_internal({"email": email})

        result = self.tables_db.list_rows(
            database_id=self.db_id,
            table_id="picker_accounts",
            queries=[
                Query.equal("email", email),
                Query.limit(1)
            ]
        )

        rows = result["rows"]
        return rows[0] if rows else None

    def get_account_by_id(
        self,
        row_id: str,
        password: Optional[str] = None,
        is_message: bool = False
    ) -> dict:
        """
        Retrieve and process a picker account by email or account ID.

        This method supports three distinct use cases:

        1. Message routing (`is_message=True`)
        - Returns only the fields required for sending messages
        - Validates account payment status
        - Decodes telegram routing data

        2. Authentication (`password` provided)
        - Validates email and password
        - Refreshes session timestamp
        - Returns an encoded session token

        3. Raw account retrieval (default)
        - Returns the full database row
        - Enforces login expiration if applicable

        Parameters:
            row_id (str):
                Email address or account identifier.

            password (str | None):
                Plain-text password for authentication.
                If None, authentication is skipped.

            is_message (bool):
                If True, returns a reduced payload for message routing only.

        Returns:
            dict:
                - Message routing payload
                - Authentication response
                - Raw account document
                - Or error information
        """

        original_input = row_id
        normalized_id = common_at_id(row_id)
        account_id = self.recover_email(normalized_id)
        current_millis = common_get_millis()

        try:
            result = self.tables_db.get_row(
                database_id=self.db_id,
                table_id="picker_accounts",
                row_id=account_id
            )

            last_seen_expired = common_minutes_after_last_update(
                result.get("millis"),
                current_millis,
                self.login_session_in_seconds
            )

            # --------------------------------------------------
            # MESSAGE ROUTING MODE
            # --------------------------------------------------
            if is_message:
                status = common_decode_internal(result["status"])["status"]

                if status != "paid":
                    if self.printer:
                        print(
                            f"\n--- ACCOUNT 01 get_account_by_id * is_message * ---\n\n{pformat(result)}\ncurrent target -> {row_id}\n---\n\n {'*'*80}\n\n"
                        )
                    return {"status": status}

                else:
                    print(
                        f"\n--- ACCOUNT 02 get_account_by_id * is_message * ---\n\n{pformat(result)}\ncurrent target -> {row_id}\n---\n\n {'*'*80}\n\n"
                    )

                decoded = {
                    "status": status,
                    "targets": common_decode_internal(result["targets"])["targets"],
                    "targets_allowed": common_decode_internal(result.get("targets_allowed", "[]")).get("targets_allowed"),
                    "account_type": common_decode_internal(result.get("account_type", "{}")).get("account_type"),
                    "balance": common_decode_internal(result.get("balance", "{}")).get("balance"),
                }

                telegram_raw = result.get("telegram_data", "[]")

                if telegram_raw == "[]":
                    decoded["telegram_data"] = []
                else:
                    decoded["telegram_data"] = common_decode_internal(
                        telegram_raw).get("telegram_data", [])

                return decoded

            # --------------------------------------------------
            # SESSION EXPIRED (NO PASSWORD)
            # --------------------------------------------------
            if last_seen_expired and password is None:
                return {
                    "error": True,
                    "message": "login expired, please login again",
                    "code": "0x0001"
                }

            # --------------------------------------------------
            # AUTHENTICATION MODE
            # --------------------------------------------------
            if password is not None:

                if self.printer:
                    print(
                        f"\n--- ACCOUNT 01 get_account_by_id * password is not None * ---\n{pformat(result)}\ncurrent target -> {row_id}\n---\n\n {'*'*80}\n\n"
                    )

                email = common_decode_internal(result["email"])["email"]
                name = common_decode_internal(result["name"])["name"]
                stored_password = common_decode_internal(
                    result["password"])["password"]
                status = common_decode_internal(result["status"])["status"]

                if original_input == email and password == stored_password:
                    self.tables_db.update_row(
                        database_id=self.db_id,
                        table_id="picker_accounts",
                        row_id=account_id,
                        data={"millis": str(current_millis)}
                    )

                    return {
                        "account": True,
                        "name": name,
                        "token": common_encode_internal({
                            "email": email,
                            "millis": current_millis,
                            "status": status
                        })
                    }

                else:
                    print(f"{'>'*80}")

                    return {
                        "account": False,
                        "error": "please confirm your password" if password != stored_password else "Please confirm your email "
                    }

            # --------------------------------------------------
            # DEFAULT: RETURN RAW DOCUMENT
            # --------------------------------------------------
            return result

        except AppwriteException as e:
            return {
                "error": True,
                "message": (
                    "email address does not exist"
                    if account_id in e.message
                    else e.message
                ),
                "code": e.code
            }

    def get_payments(self, token):

        data = common_decode_internal(token)
        current_millis = common_get_millis()
        row_id = common_at_id(data["email"])
        token_millis = data["millis"]

        result = self.tables_db.get_row(
            database_id=self.db_id,
            table_id="picker_accounts",
            row_id=row_id
        )

        common_convert_to_milliseconds = common_convert_to_milliseconds(
            token_millis, current_millis, self.login_session_in_seconds)

        if common_convert_to_milliseconds:
            return {
                "error": "login expiration",
                "message": "please login again",
                "code": "0x0001"
            }

        payments = result["payments"]

        return common_str_dict(payments) if payments == "[]" else common_decode_internal(payments)

    def update_payments(self, token, payment_data):
        """

        this method will add a new payment to the current data and
        will also encrypt the data

        payments: every 28 days

        payment data
        {
            processing data
            current millis
            next payment

        }

        current_millis + 28 * 24 * 60 * 60 * 1000



        Returns:
            True
        """

        current_payments = self.get_payments(token)["payments"]

        # print("current payemnts ")

        # pprint(current_payments)
        if "error" in current_payments:
            return current_payments

        current_millis = common_get_millis()
        next_payment = int(current_millis) + 28 * 24 * 60 * 60 * 1000
        current_payments.append(
            {
                "payment_data": payment_data,
                "current_millis": current_millis,
                "next_payment": next_payment
            }
        )

        document_id = common_at_id(common_decode_internal(token)["email"])
        created_reacord = self.tables_db.update_row(
            database_id=self.db_id,
            table_id="picker_accounts",
            row_id=document_id,
            data={"payments": common_encode_internal(
                {"payments": current_payments})},
        )

        return (created_reacord)

    def update_telegram_info(self, target: str, telegram_data: dict, update_type: str):
        """
        update_type options:
            - add_device
            - remove_device
            - update_telegram_send
        """

        target_copy = target
        account = self.get_account_by_id(target, None, True)
        normalized_id = common_at_id(target)
        account_id = self.recover_email(normalized_id)
        new_email_id_to_link = telegram_data["linked"]

        # pprint(account)

        telegram_list = common_str_dict(account.get("telegram_data", []))
        account_type = int(account.get("account_type", 1))
        targets_allowed = int(account.get("targets_allowed", 0))
        targets = int(account.get("targets", 0))
        account_types = common_str_dict(os.getenv("PRICKER_ACCOUNT_TYPES"))

        if self.printer:
            print(
                f"--- ACCOUNT 01 update_telegram_info ---\n{pformat(account)}\ncurrent target -> {target}\n---"
            )

            print(
                f"normalized_id -> {normalized_id} \naccount_id -> {account_id} \ntarget_copy -> {target_copy}\n\n")

        # -------------------------------------------------
        # OPTION B: implicit downgrade / plan mismatch
        # -------------------------------------------------

        if len(telegram_list) > targets_allowed:

            if self.printer:
                print(
                    f" telegram_list 02 {telegram_list} targets_allowed {targets_allowed}"
                )

            account["telegram_data"] = []
            account["targets"] = account_types[account['account_type']]

            update_data = {}
            for col in account:
                update_data[col] = common_encode_internal({col: account[col]})

            self.tables_db.update_row(
                database_id=self.db_id,
                table_id="picker_accounts",
                row_id=account_id,
                data=update_data
            )

            return {
                "error": True,
                "message": (
                    "Your subscription no longer supports the current Telegram devices. "
                    "All Telegram bots were removed. "
                    "Please re-add your Telegram bots."
                )
            }

        # =================================================
        # ADD DEVICE
        # =================================================
        if update_type == "add_device":
            required_keys = {"chcommon_at_id", "device_id", "send", "token"}
            if not required_keys.issubset(telegram_data):
                return {"error": True, "message": "Missing required telegram fields."}

            # 🔒 Prevent duplicate target

            if self.printer:
                print(
                    f"--- ACCOUNT add_device 01 ---\n{pformat(telegram_list)}\ncurrent target -> {target}\n\n {'*'*80}\n\n")

            if any(d.get("linked") == new_email_id_to_link for d in telegram_list):
                return {
                    "error": True,
                    "message": f"This email '{new_email_id_to_link}' is already linked to a Telegram device."
                }

            # Device limit validation
            if len(telegram_list) >= targets_allowed:
                if account_type != 5:  # NOT extra_device

                    if self.printer:
                        print(
                            f"--- ACCOUNT add_device 02 ---\n{pformat(account)}\ncurrent target -> {target}\n\n {'*'*80}\n\n")

                    return {
                        "error": True,
                        "message": "You have reached the maximum number of devices allowed; please upgrade your plan." if targets_allowed > 0 else "Please upgrade your plan"
                    }
                account["targets_allowed"] = targets_allowed + 1
                targets_allowed += 1

            # Validate Telegram
            message = self.send_telegram_message(
                telegram_data["chcommon_at_id"],
                telegram_data["token"],
                f"Picker Telegram setup successful {common_get_millis()}"
            )

            if not message:
                if self.printer:
                    print(
                        f"--- ACCOUNT add_device ---\n{pformat(account)}\ncurrent target -> {target}\n\n {'*'*80}\n\n")

                return {
                    "error": True,
                    "message": "Invalid Telegram chcommon_at_id or token."
                }

            telegram_data["linked"] = target_copy
            telegram_list.append(telegram_data)
            account["telegram_data"] = telegram_list
            account["targets"] = str(targets + 1)

            update_data = {col: common_encode_internal(
                {col: account[col]}) for col in account}

            self.tables_db.update_row(
                database_id=self.db_id,
                table_id="picker_accounts",
                row_id=account_id,
                data=update_data
            )

            if self.printer:
                print(
                    f"--- ACCOUNT add_device ---\n{pformat(account)}\ncurrent target -> {target}\n\n {'*'*80}\n\n")

            return {"error": False, "message": "Telegram device added successfully."}

        # =================================================
        # REMOVE DEVICE
        # =================================================
        elif update_type == "remove_device":
            device_id = telegram_data.get("device_id")

            # Find matching devices linked to this target
            new_list = [
                d for d in telegram_list
                if not (
                    d.get("linked") == target_copy and
                    (device_id is None or d.get("device_id") == device_id)
                )
            ]

            # Nothing removed → not found
            if len(new_list) == len(telegram_list):
                return {
                    "error": True,
                    "message": "No Telegram device found linked to this email."
                }

            removed_count = len(telegram_list) - len(new_list)

            account["telegram_data"] = new_list
            account["targets"] = str(max(0, targets - removed_count))

            update_data = {
                col: common_encode_internal({col: account[col]})
                for col in account
            }

            self.tables_db.update_row(
                database_id=self.db_id,
                table_id="picker_accounts",
                row_id=account_id,
                data=update_data
            )

            return {
                "error": False,
                "message": f"Telegram device removed successfully ({removed_count})."
            }

        # =================================================
        # ENABLE / DISABLE TELEGRAM SEND
        # =================================================
        elif update_type == "update_telegram_send":
            device_id = telegram_data.get("device_id")
            send_flag = telegram_data.get("send")

            if device_id is None or send_flag is None:
                return {
                    "error": True,
                    "message": "device_id and send flag are required."
                }

            # Normalize send flag to "yes" / "no"
            send_value = (
                "yes" if str(send_flag).lower() in {
                    "1", "true", "yes", "on"} else "no"
            )

            updated = False

            for device in telegram_list:
                if (
                    device.get("linked") == target_copy and
                    device.get("device_id") == device_id
                ):
                    device["send"] = send_value
                    updated = True
                    break

            if not updated:
                return {
                    "error": True,
                    "message": "Telegram device not found for this email."
                }

            account["telegram_data"] = telegram_list

            update_data = {
                col: common_encode_internal({col: account[col]})
                for col in account
            }

            self.tables_db.update_row(
                database_id=self.db_id,
                table_id="picker_accounts",
                row_id=account_id,
                data=update_data
            )

            return {
                "error": False,
                "message": f"Telegram send preference updated to '{send_value}'."
            }

    def send_telegram_message(self, chcommon_at_id, token, text):
        """
        Send a text message to a Telegram chat using a Bot token.

        This method sends a simple text message via the Telegram Bot API
        using the `sendMessage` endpoint.

        Parameters:
            chcommon_at_id (str | int):
                The unique identifier for the target chat or user.
                Can be a user ID, group ID, or channel ID.

            token (str):
                Telegram Bot token in the format:
                123456789:ABCdefGhIJKlmNoPQRstuVWxyz

            text (str):
                The message text to be sent.

        Returns:
            bool:
                True if the message was sent successfully, False otherwise.

        Notes:
            - This function uses JSON payloads.
            - No special headers are required by Telegram.
            - Store the bot token securely (e.g., Appwrite environment variables).
            - Supports plain text by default; formatting requires `parse_mode`.

        Example:
            send_telegram_message(
                chcommon_at_id=123456789,
                token=os.environ["TELEGRAM_BOT_TOKEN"],
                text="Record created successfully"
            )
        """

        url = f"https://api.telegram.org/bot{token}/sendMessage"

        payload = {
            "chat_id": chcommon_at_id,  # ✅ FIXED HERE
            "text": text,
            "disable_web_page_preview": True,
            "disable_notification": False
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        print(response.status_code, response.text)
        return response.ok

    def manual_updates(self, table, row_id, data):
        """
        Manually update a database row with safely encoded values.

        This method iterates over the provided data dictionary, converts each
        value into a string-safe representation using `common_dict_str`, then encodes
        each field individually using `common_encode_internal` before sending the
        update to the database.

        It is designed to ensure consistent data formatting and prevent type
        issues when updating rows (e.g. non-string values, dicts, lists, None).

        Args:
            table (str): The table ID where the row exists.
            row_id (str): The ID of the row to update.
            data (dict): A dictionary of column names and their new values.

        Returns:
            dict: The response returned by the database `update_row` operation.
        """

        _data = {}
        for k in data:
            value = data[k] if isinstance(
                data[k], str) else common_dict_str(data[k])
            _data[k] = common_encode_internal({k: value})

        # pprint(_data)

        return (self.tables_db.update_row(
            database_id=self.db_id,
            table_id=table,
            row_id=row_id,
            data=_data
        ))

    def manual_viwer(self, table="picker_accounts", email=None):

        account_id = self.recover_email(common_at_id(email))
        result = self.tables_db.get_row(
            database_id=self.db_id,
            table_id=table,
            row_id=account_id
        )

        # pprint(result)

        _data = {}

        for k in result:
            if k.startswith('$') or k == "millis" or k == "password":
                pass
            else:
                # print(common_decode_internal(result[k]))
                _data[k] = common_decode_internal(result[k])[k]

        return _data

    def create_cellphone_token(self, email):
        return common_encode_internal({
            "email": email,
            "account_exists": True
        })


def get_account_by_id(id="eggsteban@gmail.com", password=None, is_message=True):
    """
    this method returs
    {'account': True,
     'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3QwN0BnbWFpbC5jb20iLCJtaWxsaXMiOjE3NjgyNTQzMjA4ODV9.9ou2s6uuO5COdBjN1kpLB1Vry0iT0L7jS23iUovvlxA'}
    """

    api = Main()
    return api.get_account_by_id(id, password, is_message)


def get_account(id="test07@gmail.com"):
    api = Main()
    return api.get_account(id)


def get_pending_documents(token):
    api = Main()
    return api.get_pendings_with_fallback_and_update(token)


def save_picker_text(data: Optional[Dict] = None):
    """_summary_

    data:   
        email
        text
        token: will also contain the email that the text will be saved 

    Returns:
        _type_: _description_
    """

    if data is None:
        data = {}

    api = Main()
    # target = data.get("email")
    decoded_token = common_decode_internal(data.get("token", None))

    if not decoded_token or decoded_token is None:
        return

    target = decoded_token.get("email")

    # this is getting the account to post a messege
    account = api.get_account_by_id(target, None, True)

    if api.printer:
        print(
            f"--- ACCOUNT ---\n{pformat(account)}\ncurrent target -> {target}\n---"
        )

    # Account must be paid
    if account.get("status") != "paid":
        return

    telegram_data = account.get("telegram_data", [])
    targets = int(account.get("targets", 0))

    email_id_ = api.extract_email_id(target)
    email_id_ = int(email_id_) if email_id_ is not None else 0

    if api.printer:
        print(
            f"--- ROUTING DEBUG ---\n"
            f"email_id_ -> {email_id_}\n"
            f"targets  -> {targets}\n"
            f"telegram_data ->\n{pformat(telegram_data)}\n"
            f"--------------------"
        )

    # -------------------------
    # Device not allowed by plan
    # -------------------------
    if targets == 0 and email_id_ > 0:
        return

    telegram_message_sent = False

    for telegram_bot in telegram_data:
        if (
            int(telegram_bot.get("device_id", -1)) == email_id_
            and telegram_bot.get("send", "").lower() == "yes"
        ):
            api.send_telegram_message(
                telegram_bot["chcommon_at_id"],
                telegram_bot["token"],
                data.get("text", "")
            )
            telegram_message_sent = True
            break

    # -------------------------
    # Fallback → save record
    # -------------------------
    if not telegram_message_sent:
        return api.create_record(data=data)


def create_account(data={"email": "eggsteba23@gmail.com", "password": "eggsteba23@gmail.com", "name": "Esteban"}):
    return common_create_record("picker_accounts", data)


def login(data):
    api = Main()
    return api.get_account_by_id(data["email"], data["password"])


def get_payments(token):
    api = Main()
    return api.get_payments(token)


def update_payments(token, data):
    api = Main()
    return api.update_payments(token, data)


def update_telegram_info(self, target: str, telegram_data: Dict, update_type: str):
    api = Main()
    return api.update_telegram_info(target, telegram_data, update_type)


def manual_updates(table, row_id, data):
    api = Main()
    pprint(api.manual_updates(table, row_id, data))


def manual_viwer(tablem, email):
    api = Main()
    pprint(api.manual_viwer(tablem, email))


def get_messages(email, from_idx, to_idx):
    api = Main()
    return api.get_new_messages_range(email, from_idx, to_idx)


def create_cellphone_token(email):
    api = Main()
    return api.create_cellphone_token(email)


if __name__ == "__main__":
    pass

    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImVnZ3N0ZWJhbkBnbWFpbC5jb20iLCJtaWxsaXMiOjE3Njk1NDYxMDg2MjQsInN0YXR1cyI6InBhaWQifQ.XvEMX2OyEY_dCNLjCabidqFw53C1z60mkaRROhuii-M'
    data = {
        "email": "eggsteban@gmail.com",
        "password": "eggsteban0@gmail.com",
        "type": f"update test just now  {common_get_millis()}"
    }

    pprint(get_account_by_id())
    # pprint(login(data))
    # pprint(get_messages("eggsteban@gmail.com", 0, 100))
    # cell_token = (create_cellphone_token("eggsteban@gmail.com"))
    # pprint(cell_token)
    # pprint(Main().common_decode_internal(cell_token))
    # print(create_account())
