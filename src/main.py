import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common_functions as cf


# -------------------------------
# Response Helper
# -------------------------------
def response(data, status=200):
    return {
        "status": status,
        "body": json.dumps(data),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Content-Type": "application/json",
        },
    }


# -------------------------------
# Request Parser
# -------------------------------
def parse_body(body):
    if isinstance(body, str):
        try:
            return json.loads(body)
        except:
            return {}
    return body or {}


# -------------------------------
# Decode Stored JSON
# -------------------------------
def decode_record(record):
    try:
        return json.loads(record["data"]["data"])
    except:
        return record["data"]["data"]


# -------------------------------
# Database Fetch
# -------------------------------
def fetch(collection_id, document_id):
    record = cf.common_get_record(collection_id, document_id)

    if not record or "data" not in record:
        return response({"error": "Record not found"}, 404)

    return response(decode_record(record))


# -------------------------------
# Route Handlers
# -------------------------------
def leagues_by_country(data):
    return fetch("6766ef78000d7daec880", "leaguesInCountry")


def all_public(data):
    return fetch("mam_public_all", "all_public_1")


def teams_of_league(data):
    return fetch(
        os.getenv("get_teams_in_league_collection_id"),
        f"mam_league_{data['leagueId']}",
    )


def next_games(data):
    return fetch(
        os.getenv("next_games_collection_id"),
        data["teamId"],
    )


# -------------------------------
# Route Map
# -------------------------------
ROUTES = {
    "leaguesByCountry": leagues_by_country,
    "allPublic": all_public,
    "getTeamOfLeague": teams_of_league,
    "nextGames": next_games,
}


# -------------------------------
# Main Function
# -------------------------------
def main(context):

    context.log(f"Function executed with method: {context.req.method}")

    if context.req.method not in ["GET", "POST"]:
        return response({"error": "Method not allowed"}, 405)

    data = parse_body(context.req.body)

    try:

        update = data.get("update")

        handler = ROUTES.get(update)

        if not handler:
            return response({"error": "Invalid update parameter"}, 400)

        return handler(data)

    except Exception as e:

        context.error(str(e))

        return response(
            {"error": "Internal server error", "details": str(e)},
            500,
        )
