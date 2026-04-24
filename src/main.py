import json
from pprint import pprint
import xml.etree.ElementTree as ET
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from utils import *  # Ensure all necessary imports are available in utils.py
from rentals import *
from mam import *
from managerAi import *
from cc_payments import *
from openAi import *
from picker import *


def main(context):
    context.log(f"Function executed with the following context:")
    context.log(f"\n\tReceived request method: {context.req.method}")

    def create_response(data, status=200):
        response_body = json.dumps(data)
        response = {
            "status": status,
            "body": response_body,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Content-Type": "application/json",
            },
        }

        print("response sending out ")
        pprint(response)
        return response

    def confirm_is_same_ip(client_ip, request_ip):
        return client_ip == request_ip

    if context.req.method == "POST":
        client_ip = "Unknown IP"

        try:
            # 1. Improved IP detection for Appwrite Cloud
            client_ip = context.req.headers.get("x-appwrite-client-ip") or \
                        context.req.headers.get("x-forwarded-for", "Unknown IP")
            client_ip = client_ip.split(",")[0].strip()

            # 2. FIX: Safely parse the body if it is a string
            data = context.req.body
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception as json_err:
                    context.error(f"Failed to parse JSON: {json_err}")
                    return create_response({"error": "Invalid JSON string"}, 400)

            # 3. Now this assignment will work because 'data' is a dict
            if client_ip == "Unknown IP":
                # Changed from "i" to "ip_missing" for easier debugging
                return create_response({"error": "ip_missing"}, 900)
            else:
                data["ip"] = client_ip.replace(":", ".")

            context.log(f"Processing request for IP: {client_ip}")

        except Exception as e:
            context.error(f"Error reading request body: {e}")
            return create_response({"error": "Body parsing failed", "details": str(e)}, 400)

        # Check if all required keys are present
        # Check if all required keys are present and have non-empty values
        try:

            if data.get("update") != "confirm_key":
                context.log("------------------key------------------------")
                # Define the required keys
                required_keys = ["key", "document_id", "update", "collection"]

                # Find missing or empty keys
                missing_or_empty_keys = [
                    key for key in required_keys if not data.get(key)
                ]

                # Check if there are any missing or empty keys
                if missing_or_empty_keys:
                    error_message = f"Missing or empty required data keys: {', '.join(missing_or_empty_keys)}"
                    context.error(error_message)

                    # handle strike webhook updates
                    if "webhookVersion" in data:
                        pprint(data)
                        return context.res.empty()

                    if data["update"] == "allPublic":
                        pass

                    else:
                        return create_response({"error": "Missing or empty required data"}, 400)

                context.log("------------------key done -------------------")

            if data.get("update") == "one_create_user":  # Add this if statement
                context.log("Attempting to create a user for 'one'...")

                try:
                    response = create_one_user(
                        data["email"],
                        data["password"],
                    )
                    context.log(f"User creation response: {response}")
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error creating user: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {"error": "Error creating user",
                            "details": str(e)}, 500
                    )

            if data.get("update") == "get_one_account":  # Add this if statement
                context.log("Attempting to get a user for 'one'...")

                try:
                    response = get_one_account(
                        data["email"],
                        data["password"],
                    )
                    context.log(f"User creation response: {response}")
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error creating user: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {"error": "Error creating user",
                            "details": str(e)}, 500
                    )

            if data["update"] == "get_client":
                if (
                    "key" in data
                    and is_key_valid(data["key"])
                    and len(data["collection"])
                    and len(data["document_id"])
                ):
                    context.log("Keys confirmed ...!")
                    try:
                        # Fetch the document
                        client = get_document(
                            data["collection"], data["document_id"])
                        context.log(f"Fetched client: {client}")
                        return create_response(client)
                    except Exception as e:
                        context.error(f"Error fetching document: {e}")
                        return create_response(
                            {"error": "Error fetching document",
                                "details": str(e)}, 500
                        )
                else:
                    context.log("A key has not been found")
                    return create_response({"error": "Key not found"}, 404)

            if data["update"] == "update_client":
                if (
                    "key" in data
                    and is_key_valid(data["key"])
                    and len(data["collection"])
                    and len(data["document_id"])
                ):
                    context.log("Keys confirmed at update_client...!")

                    try:
                        # Fetch the document
                        dataToUpdate = update_documents(
                            data["collection"],
                            data["document_id"],
                            data["data_to_update"],
                        )
                        context.log(f"Data to update: {dataToUpdate}")
                        context.log(
                            f"seinding history doc id: {data['document_id']}")
                        context.log(
                            f"seinding history data to update : {data['data_to_update']['current_visit']}"
                        )

                        if "close" in data and data["close"]:
                            history = update_history(
                                data["document_id"],
                                data_to_update=data["data_to_update"]["current_visit"],
                            )
                            context.log(f"Data to update history: {history}")

                            return create_response(history)

                        return create_response(dataToUpdate)
                    except Exception as e:
                        context.error(f"Error fetching document: {e}")
                        return create_response(
                            {"error": "Error fetching document",
                                "details": str(e)}, 500
                        )

                else:
                    context.log("A key has not been found")
                    return create_response({"error": "Key not found"}, 404)

            if data["update"] == "confirm_key":
                context.log("Key confirmed ...!")
                try:
                    r = is_key_valid(data["key"])
                    context.log(f"Confirmation of key: {r}")
                    return create_response({"is_key": r})
                except Exception as e:
                    context.error(f"Error fetching key: {e}")
                    return create_response(
                        {"error": "Error fetching key", "details": str(e)}, 500
                    )

            if data["update"] == "create_client":
                if (
                    "key" in data
                    and is_key_valid(data["key"])
                    and len(data["collection"])
                    and len(data["document_id"])
                ):

                    context.log(f"create_client doc id: {data['document_id']}")
                    context.log(
                        f"create_client Data to update: {data['data_to_update']}"
                    )
                    context.log(
                        f"create_client current_visit : {data['data_to_update']['current_visit']}"
                    )

                    return create_response(
                        create_document(
                            data["collection"],
                            data["document_id"],
                            data["data_to_update"],
                        )
                    )

                else:
                    context.log("A key has not been found")
                    return create_response({"error": "Key not found"}, 404)

            if data["update"] == "sendEmailToResetPassword":

                context.log("sending email containg key for new password")

                try:
                    response = send_email(
                        data["email"],
                        data["lang"],
                        data["password"],
                    )
                    context.log(f"email sent")
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error creating user: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {"error": "Error creating user",
                            "details": str(e)}, 500
                    )

            if data["update"] == "confirmPassword":

                print("init confirmPassword")

                try:
                    response = verify_token(
                        data["token"], data["password"], data["reset"], data["email"]
                    )
                    print(f"password reset")
                    print(response)
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error creating user: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": (
                                "Your password did not math !!!"
                                if data["lang"] == "en"
                                else "La clave que enviastes no es igual a la anterior"
                            ),
                            "details": str(e),
                        },
                        500,
                    )

            # -------------------------------------------------------------------------------
            # rentals
            # -------------------------------------------------------------------------------

            if data["update"] == "createLandLord":

                doc_id = at_id(data["email"])
                new_data = data["new_data"]
                collection_id = data["id"]

                try:
                    response = create_document(collection_id, doc_id, new_data)
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error creating land lord: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": (
                                "Land Lord Account has not been created"
                                if data["lang"] == "en"
                                else "La cuenta de administrado no fue creada"
                            ),
                            "details": str(e),
                        },
                        500,
                    )

            # -------------------------------------------------------------------------------
            # picker
            # -------------------------------------------------------------------------------

            if data["update"] == "save_piker_text":

                try:
                    l = ["update", "key", "document_id", "collection", "ip"]
                    for name in l:
                        data.pop(name, None)

                    response = save_picker_text(data)
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 01: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": True,
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "get_piker_account_by_target":

                try:
                    l = ["update", "key", "document_id", "collection", "ip"]
                    for name in l:
                        data.pop(name, None)

                    response = get_account_by_id(
                        data["id"], data["password"], is_message=True)
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 01: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": True,
                            "details": str(e),
                        },
                        500,
                    )

            # -------------------------------------------------------------------------------
            # Mano a Mano
            # -------------------------------------------------------------------------------

            if data["update"] == "leaguesByCountry":

                try:
                    response = get_lbc(data)
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 01: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("01"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "getTeamOfLeague":

                try:
                    response = get_tol(data["leagueId"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 02: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("02"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "nextGames":

                try:
                    response = get_ng(
                        data["teamId"],
                        data["next"],
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 03: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("03"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "mamLogin":

                try:
                    response = get_mam_account_two(
                        {
                            "email": data["email"],
                            "password": data["password"],
                            "ip": data["ip"]
                        },
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 04: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("04"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "mamCreateAccount":

                try:
                    response = create_mam_login_two(
                        {
                            "email": data["email"],
                            "user_name": data["user_name"],
                            "password": data["password"],
                            "referred_by": data["referred_by"],
                        }
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 05: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("05"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "addFavs":

                try:
                    public_key = data.get("public_key") or "key"

                    response = update_favs(
                        {
                            "email": data["email"],
                            "account_id": data["account_id"],
                            "fav_teams": data["fav_teams"],
                            "public_key": public_key,
                        }
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 05: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("addFavs"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "teamName":

                try:
                    response = get_tn(data["teamId"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 05: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("teamName"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "createEscrow":

                try:
                    response = create_escrow(
                        data["fixture_id"],
                        data["save_type"],
                        data["creator"],
                        data["creator_side"],
                        data["save_amount"],
                        False,
                        False,
                        None,
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 05: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("createEscrow"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "acceptEscrow":

                try:
                    response = create_escrow(
                        data["fixture_id"],
                        data["save_type"],
                        data["creator"],
                        data["creator_side"],
                        data["save_amount"],
                        False,
                        True,
                        data["save_id"],
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 05: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("acceptEscrow"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "allEscrowHistory":

                try:
                    response = get_escrow_history(
                        data["email"],
                        data["account_id"],
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error allEscrowHistory: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "allEscrowHistory",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "depositCryptoList":

                try:
                    response = deposit_list()
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error depositCryptoList: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "depositCryptoList",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "btcLightingAddress":

                try:
                    response = get_btc_lightning_address(data["amount"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error btcLightingAddress: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "btcLightingAddress",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "tronAddress":

                try:
                    response = get_new_tron_addres()
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error tronAddress: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "tronAddress",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "getAddress":

                try:

                    if data["type"] == "USDT - Tron":
                        response = get_new_tron_addres(data)
                        return create_response(response)

                    elif data["type"] == "BTC - Lightning":
                        response = get_btc_lightning_address(
                            data["email"], data["id"], data["amount"],  data["key"])
                        return create_response(response)

                except Exception as e:
                    context.error(f"Error tronAddress: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "tronAddress",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "genQr":

                try:
                    qr_string = generate_qr(
                        data["email"],
                        data["account_id"],
                        data["content"],
                        data["key"],
                    )
                    return create_response({"qr": qr_string})

                except Exception as e:
                    context.error(f"Error genQr: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "genQr",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "allPublic":

                try:
                    all_documents_from_collection = get_all_public_saves(
                        data["ip"])
                    return create_response({"allPublic": all_documents_from_collection})

                except Exception as e:
                    context.error(f"Error allPublic: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "allPublic",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "thisLiveTest":

                try:
                    response = get_mam_account_three(
                        data["data"]
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 05: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("thisLiveTest"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "creatEscrowForPublic":

                try:
                    response = create_mam_public_escrow(data)
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 05: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("creatEscrow forPublic"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "createBolt":

                try:
                    response = create_mam_public_escrow(data["data"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error createBolt: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("createBolt forPublic"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] in ["updateBolt", "closeBolt"]:

                try:
                    response = update_mam_bolt(data["data"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error updateBolt: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("updateBolt forPublic"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "getIcons":

                try:
                    response = get_bolt_icons(data["key"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error updateBolt: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("updateBolt forPublic"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "withdrawal":

                try:
                    response = request_withdraw(data)
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error updateBolt: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("updateBolt forPublic"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "getMamLightingPaymentStatus":

                try:
                    response = get_mam_lightning_status(
                        email, id, strike_invoice_id=None, key=None
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error get_mam_lightning_status: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("get_mam_lightning_status forPublic"),
                            "details": str(e),
                        },
                        500,
                    )

            # -------------------------------------------------------------------------------
            # Any payments transaction
            # -------------------------------------------------------------------------------

            if data["update"] == "process_payment":

                try:
                    response = make_cc_payment(data["payment_data"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 05: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("process_payment"),
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "transaction_status":

                try:
                    response = check_transaction_status(
                        data["id"], data["applicativo"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error 05: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": ("transaction_status"),
                            "details": str(e),
                        },
                        500,
                    )

            # -------------------------------------------------------------------------------
            # sivar emergency
            # -------------------------------------------------------------------------------

            if data["update"] == "sivarPayment":

                try:
                    url = "https://sivar.malkiamed.dev/api/v1/payment-link"
                    headers = {"Content-Type": "application/json"}

                    # Multiply payment by 100 and convert to an integer
                    data = {
                        "amount": int(data["amount"] * 100),
                        "name": data["name"],
                    }

                    # Send POST request
                    response = requests.post(url, headers=headers, json=data)

                    print("Raw Response Text:", response.text)

                    # Remove surrounding quotes if they exist
                    cleaned_response = response.text.strip('"')

                    try:
                        # Parse the cleaned XML response
                        root = ET.fromstring(cleaned_response)

                        # Extract required fields
                        order_id = root.find(".//OrderID").text
                        session_id = root.find(".//SessionID").text
                        base_url = root.find(".//URL").text

                        # Construct the link
                        link = f"{base_url}?ORDERID={order_id}&SESSIONID={session_id}"
                        print("Generated Link:", link)
                        return create_response(
                            {"link": link, "id": order_id, "session": session_id}
                        )

                    except ET.ParseError as e:
                        print("Failed to parse XML:", e)
                        return create_response(
                            {
                                "error": "XMLParsingError",
                                "details": str(e),
                            },
                            500,
                        )

                except Exception as e:
                    context.error(f"Error sivarPayment: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "sivarPayment",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "sivarOrderStatus":

                try:
                    url = "https://sivar.malkiamed.dev/api/v1/check-usd-payment-status"
                    headers = {"Content-Type": "application/json"}

                    # Multiply payment by 100 and convert to an integer
                    data = {
                        "session": data["session"],
                        "order_id": data["order_id"],
                    }

                    response = requests.post(
                        url, headers=headers, json=data).json()
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error sivarOrderStatus: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "sivarOrderStatus",
                            "details": str(e),
                        },
                        500,
                    )

            # -------------------------------------------------------------------------------
            # soccere AI
            # -------------------------------------------------------------------------------

            if data["update"] == "managerLogin":

                try:
                    response = login_to_manager_ai_account(
                        {
                            "email": data["email"],
                            "password": data["password"],
                        },
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error managerLogin: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "managerLogin",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "managerCreateAccount":

                try:
                    response = create_manager_ai_account(
                        {
                            "email": data["email"],
                            "password": data["password"],
                        },
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error create_manager_ai_account: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "create_manager_ai_account",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "getManagerTeamsOfLeague":

                try:
                    response = get_manager_teams_in_league(
                        data["id"], data["key"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error getManagerTeamsOfLeague: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "getManagerTeamsOfLeague",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "getNextGames":

                try:
                    response = get_manager_next_games(
                        data["id"], data["nextGames"], data["key"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error getNextGames: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "getNextGames",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "getLineUp":

                try:
                    response = get_manager_line_up(data["id"], data["key"])
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error getLineUp: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "getLineUp",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "getPricePlanAndNames":

                try:
                    response = get_price_plans_and_names()
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error getPricePlanAndNames: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "getPricePlanAndNames",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "resetPassword":

                try:

                    user_email = data["email"]
                    new_data = {
                        "email": user_email,
                        "password": "",
                    }
                    account_exits = login_to_manager_ai_account(new_data)
                    if "Invalid Email address" in account_exits:
                        return account_exits

                    response = send_manager_reset_password_link(
                        user_email,
                        "reset_password_email",
                        "Reset Password",
                        {
                            "emailTitle": "Reset Password",
                            "EmailBody": "Thank you for joing us "
                        },
                        "one"
                    )
                    return create_response(response)

                except Exception as e:
                    context.error(
                        f"Error send_manager_reset_password_link: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "send_manager_reset_password_link",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "updatePasswordManually":

                try:
                    token = data["token"]
                    new_password = data["newPassword"]
                    is_valid_token = decode_token_manager_ai_token(token)

                    if is_valid_token and "email" in is_valid_token:
                        set_new_password = update_manager_ai_password(
                            is_valid_token["email"], new_password)
                        return create_response(True if "created" in set_new_password else False)

                except Exception as e:
                    context.error(f"Error updatePasswordManually: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "updatePasswordManually",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "getManagerCryptoList":

                try:
                    token = data["key"]

                    return create_response(
                        get_manager_deposit_crypto_list(token)
                    )

                except Exception as e:
                    context.error(f"Error getManagerCryptoList: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "getManagerCryptoList",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "getManagerCryptPaymentAddress":

                try:
                    token = data["key"]
                    amount = data["amount"]
                    name = data["name"]
                    this_type = data["cryptoType"]

                    if this_type == "BTC - Lightning":

                        return create_response(
                            get_manager_lightning_address(amount, token, name)
                        )

                    if this_type == "USDT - Tron":
                        wallet = get_manager_usdt_tron_address(data["key"])
                        return create_response({"address": wallet["base58check_address"], "qr": wallet["qr"]})

                except Exception as e:
                    context.error(f"Error getManagerCryptPaymentAddress: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "getManagerCryptPaymentAddress",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "2dayGames":

                try:
                    return create_response(
                        today_games()
                    )
                except Exception as e:
                    context.error(f"Error 2dayGames: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "2dayGames",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "lightningStatus":

                try:
                    return create_response(
                        get_manager_lightning_status(data["id"], data["plan"])
                    )
                except Exception as e:
                    context.error(f"Error lightningStatus: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "lightningStatus",
                            "details": str(e),
                        },
                        500,
                    )

            if data["update"] == "tronStatus":

                try:
                    return create_response(
                        get_manager_usdt_balance(data["wallet"], data["key"])
                    )
                except Exception as e:
                    context.error(f"Error tronStatus: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {
                            "error": "tronStatus",
                            "details": str(e),
                        },
                        500,
                    )
            # Return statement for when no valid response is generated
            return context.res.empty()

        except Exception as e:
            context.error(f"Error processing request: {e}")
            import traceback

            error_message = traceback.format_exc()
            context.error(f"Traceback: {error_message}")
            return create_response(
                {"error": "Error processing request", "details": str(e)}, 400
            )

    else:
        context.error("Unsupported request method")
        return create_response("supported", 405)
