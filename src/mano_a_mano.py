import json
import sys
import os
import requests
import time
import copy
from pprint import pprint
from collections import defaultdict
from datetime import datetime
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common_functions as cf

# -------------------------------
# Api football
# -------------------------------

live_by_game_status = [
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
not_live_by_game_status = [
    "Match Finished",
    "Match Postponed",
    "Match Cancelled",
    "Match Abandoned",
    "Technical Loss",
    "WalkOver",
]

api_url = os.getenv("apiFootball")
football_api_key = os.getenv("football_api_key")


def api_leagues_by_country():
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

    url = f"{api_url}leagues"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": football_api_key,
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

    main_leagues = cf.common_get_record("data_env", "important_leagues")
    main_leagues = json.loads(main_leagues["data"]["data"])
    leagues_by_country = defaultdict(list)

    # Aggregate leagues by country

    for league_data in data["response"]:
        country_name = league_data["country"]["name"]
        league_info = {
            "id": league_data["league"]["id"],
            "name": league_data["league"]["name"],
            "league_img": league_data["league"]["logo"],
            "contry_img": league_data["country"].get("flag")
            or "https://sistemasintegradosao.com/assets/img/siaoLogos/logoX512.png",
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

        if league["name"] in [
            "Friendlies",
        ]:
            league.update({"name": "FIFA", "contry_img": league["league_img"]})
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


def get_all_public_saves(fixed: bool = False):
    """
    Retrieve public saves from the database.

    Parameters
    ----------
    fixed : bool, optional
        - False (default):
            Returns the aggregated public saves stored in the
            `mam_public_all` table under row `all_public_1`.
            The stored JSON string is parsed and returned as a dictionary.

        - True:
            Retrieves all rows from the `mam_public_saves` table,
            parses the JSON stored in `data.data`, and returns the
            results as a dictionary keyed by each save `id`.

    Returns
    -------
    dict
        A dictionary containing the public saves.

        When `fixed=False`:
            {
                "SAVE_ID": {save_data},
                ...
            }

        When `fixed=True`:
            {
                "SAVE_ID": {save_data},
                ...
            }

        Returns an empty dictionary `{}` if no records are found.
    """

    if not fixed:
        table = "mam_public_all"
        print(f"[EXECUTING FIXED ] Table -> {table}")
        record = cf.common_get_record("mam_public_all", "all_public_1")

        if not record:
            return {}

        data = record.get("data", {}).get("data")

        if isinstance(data, str):
            return json.loads(data)

        return data or {}

    else:
        table = "mam_public_saves"
        print(f"[EXECUTING FIXED ] Table {table}")
        records = cf.common_get_all_records("mam_public_saves")

        result = {}

        for r in records:
            data_field = r.get("data", {}).get("data")

            if isinstance(data_field, str):
                try:
                    parsed = json.loads(data_field)
                except json.JSONDecodeError:
                    continue
            else:
                parsed = data_field

            if isinstance(parsed, dict) and "id" in parsed:
                result[parsed["id"]] = parsed

        return result


def get_teams_of_league(league_id):
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

    print(f"get_teams_of_league with league {league_id}")

    season = datetime.now().year - 1

    apiUrl = os.getenv("apiFootball")
    url = f"{apiUrl}teams"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": football_api_key,
    }
    params = {
        "league": league_id,
        "season": season,
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        if "response" in data:
            # Sort the 'response' field by team name
            data["response"] = sorted(data["response"], key=lambda x: x["team"]["name"])

            ADD_NEXT_ROUND_GAMES = (
                os.getenv("add_next_round_games", "false").lower() == "true"
            )

            if ADD_NEXT_ROUND_GAMES:

                # Create a new entry instead of modifying the existing one
                sample = copy.deepcopy(data["response"][0])
                sample["team"]["code"] = "NR"
                sample["team"]["name"] = "Next Round Games"
                sample["team"]["id"] = cf.common_encode_dict(
                    {
                        "league_id": f"NR{league_id}",
                        "teams_len": len(data["response"]) / 2,
                    }
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


def get_next_round(league_id=2):

    teams_len = 20

    print(f"getting next round games for {league_id} and len {teams_len}")
    if "NR" in str(league_id):
        league_id = re.sub(r"\D", "", league_id)

    print(f"getting next round games for second time {league_id} and len {teams_len}")

    next_round_recods = cf.common_get_record(
        os.getenv("get_teams_in_league_collection_id"), league_id
    )

    print("next_round_recods")
    pprint(next_round_recods)

    url = f"{api_url}fixtures?league={league_id}&next={teams_len + (teams_len // 2)}"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": football_api_key,
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: Unable to fetch leagues. Status code: {response.status_code}")
        print(f"Response: {response.text}")

        # If we've reached this point, return the default dict
        return {
            "future": {
                "get": "fixtures",
                "parameters": {"team": f"NR{league_id}", "next": 1},
                "errors": [],
                "results": 1,
                "paging": {"current": 1, "total": 1},
                "response": [],
            },
            "past": {
                "get": "fixtures",
                "parameters": {"team": f"NR{league_id}", "next": 1},
                "errors": [],
                "results": 0,
                "paging": {"current": 1, "total": 1},
                "response": [],
            },
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
            "parameters": {"team": f"NR{league_id}", "next": f"{mid_point}"},
            "errors": [],
            "results": mid_point * 2,
            "paging": {"current": 1, "total": 1},
            "response": data["response"],
        },
        "past": {
            "get": "fixtures",
            "parameters": {"team": f"NR{league_id}", "next": f"{mid_point}"},
            "errors": [],
            "results": 0,
            "paging": {"current": 1, "total": 1},
            "response": [],
        },
    }


def get_next_games(team_id=50):
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
    next_len = 3

    if len(str(team_id)) > 10:  # if id > 10 this meand i am decodeing a jwt
        data = cf.commond_decode_data(team_id)
        league_id = data["league_id"]
        teams_len = int(data["teams_len"])
        return get_next_round(league_id)

    # API details
    url = f"{api_url}fixtures"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": football_api_key,
    }

    # Parameters for past and future fixtures
    params_past = {"team": team_id, "last": next_len}
    params_future = {"team": team_id, "next": next_len}

    # Retry logic for past fixtures
    response_past = None
    for attempt in range(5):
        response_past = requests.get(url, headers=headers, params=params_past).json()
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
        print(f"Attempt {attempt + 1} (future fixtures): Retrying in 1 second...")
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
            if f["fixture"]["status"]["long"] in live_by_game_status
        ]
        other_fixtures = [
            f
            for f in fixture_list
            if f["fixture"]["status"]["long"] not in live_by_game_status
        ]
        return live_fixtures + other_fixtures

    # Reorder the response field if it exists
    if "response" in response_past:
        response_past["response"] = reorder_fixtures(response_past["response"])
    if "response" in response_future:
        response_future["response"] = reorder_fixtures(response_future["response"])

    # Check if the first fixture in response_past is live
    if (
        "response" in response_past
        and response_past["response"]
        and response_past["response"][0]["fixture"]["status"]["long"]
        in live_by_game_status
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

jobs = {
    "leaguesByCountry": {
        "handler": api_leagues_by_country,
        "kwargs": {},
        "interval": {"hours": 24},
        "cols_to_update": ["data", "today", "counter"],
        "updates": True,
    },
    "allPublic": {
        "handler": get_all_public_saves,
        "kwargs": {},
        "interval": {"minutes": 1},
        "cols_to_update": ["data", "today", "counter"],
        "updates": False,
    },
    "getTeamOfLeague": {
        "handler": get_teams_of_league,
        "kwargs": {"league_id": "140"},
        "interval": {"days": 7},
        "cols_to_update": ["data", "today", "counter"],
        "updates": True,
    },
    "nextGames": {
        "handler": get_next_games,
        "kwargs": {"team_id": "140"},
        "interval": {"days": 1},
        "cols_to_update": ["data", "today", "counter"],
        "updates": True,
    },
}


def fetch(collection_id: str, document_id: str, update: str):
    """
    Generic cache fetcher with auto-create and timed updates.
    """

    def p(msg):
        print(f"[AT FETCH] -> {msg}\n\n")

    now = cf.common_get_millis()
    job = jobs.get(update)

    if not job:
        return {"error": "Invalid update job"}, 400

    p(f"\tcollection_id {collection_id}\tdocument_id {document_id}")

    record = cf.common_get_record(collection_id, document_id)

    handler = job["handler"]
    args = job.get("args", ())
    kwargs = job.get("kwargs", {})
    cols = job.get("cols_to_update", [])

    interval = job.get("interval")
    updates_enabled = job.get("updates", True)

    # ------------------------------------------------------------
    # RECORD EXISTS → CHECK CACHE
    # ------------------------------------------------------------
    if record:

        p("Record exists")

        today = record.get("today")
        counter = record.get("counter", 0)

        is_millis = cf.common_ensure_millis(today)
        should_update = True

        if interval and today and is_millis:
            should_update = cf.common_time_passed(int(today), interval)

        if not should_update or not updates_enabled:
            print(f"[CACHE] {document_id}")
            return decode_record(record)

    else:
        counter = 0

    # ------------------------------------------------------------
    # RUN HANDLER
    # ------------------------------------------------------------
    print(f"[HANDLER] {handler.__module__}.{handler.__name__}")
    print(f"[HANDLER ARGS] args={args} kwargs={kwargs}")
    result = handler(*args, **kwargs)

    if not result:
        return {"error": "Handler returned no data"}, 500

    # ------------------------------------------------------------
    # BUILD PAYLOAD
    # ------------------------------------------------------------
    payload = {}

    for col in cols:

        if col == "data":
            payload["data"] = cf.common_dict_str(result)

        elif col == "today":
            payload["today"] = str(now)

        elif col == "counter":
            payload["counter"] = counter + 1

    # ------------------------------------------------------------
    # WRITE DATABASE
    # ------------------------------------------------------------
    if record:
        cf.common_update_record(collection_id, document_id, payload)
        print(f"[UPDATED] {document_id}")

    else:

        _new_doc_id = "next_games_team_"
        if _new_doc_id in document_id:
            _name = document_id.split(_new_doc_id)[1]
            print(f"_name {_name}")
            if len(str(_name)) > 10:
                document_id = (
                    f"{_new_doc_id}{cf.commond_decode_data(_name)['league_id']}"
                )

        cf.common_create_record(collection_id, payload, document_id)
        print(f"[CREATED] {document_id}")

    return result


# -------------------------------
# Route Handlers
# -------------------------------
def leagues_by_country(data):
    _id = os.getenv("leages_by_country_collection_id")
    return fetch(_id, "leaguesInCountry", data["update"])


def all_public(data):
    return fetch("mam_public_all", "all_public_1", data["update"])


def teams_of_league(data):
    # print (f"current league in file {jobs[data['update']]['kwargs']['league_id']}")
    jobs[data["update"]]["kwargs"]["league_id"] = data["leagueId"]
    # print (f"target league in file {jobs[data['update']]['kwargs']['league_id']}")
    # pprint (jobs)
    return fetch(
        os.getenv("get_teams_in_league_collection_id"),
        f"mam_league_{data['leagueId']}",
        data["update"],
    )


def next_games(data):

    team_id = data["teamId"]
    jobs[data["update"]]["kwargs"]["team_id"] = team_id

    # if len(str(team_id)) > 10:  # if id > 10 this meand i am decodeing a jwt

    #     # {'leagueId': 331,
    #     # 'teamId': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsZWFndWVfaWQiOiJOUjIiLCJ0ZWFtc19sZW4iOjQxLjB9.IG9TaXjg05K_vF6FPJuAkYa8lISGaP2qUmYR_OGkZqo',
    #     # 'update': 'nextGames'}

    #     # this data {'league_id': 'NR2', 'teams_len': 41.0}

    #     data = cf.commond_decode_data(team_id)
    #     return (get_next_round(data['league_id']))

    return fetch(
        os.getenv("next_games_collection_id"),
        f"next_games_team_{data['teamId']}",
        data["update"],
    )


def create_account(data):

    uid = cf.common_generate_payment_token(39999999)["token"]
    now = cf.common_get_millis()
    id = cf.common_at_id(data["email"])

    for key in list(data.keys()):

        # -------------------------
        # ACCOUNT ID
        # -------------------------
        if key == "account_id":
            data[key] = cf.common_encode_one_value(
                {key: cf.common_at_id(data["email"])}
            )

        # -------------------------
        # ACCOUNT VERIFIED
        # -------------------------
        elif key == "account_verified":
            data[key] = cf.common_encode_one_value({key: False})

        # -------------------------
        # AVATAR
        # -------------------------
        elif key == "avatar":
            avatar = f"https://ui-avatars.com/api/?name={data['first_name']}+{data['last_name']}&background=F2C94C&color=fff&bold=true&rounded=true&format=svg"
            data[key] = cf.common_encode_one_value({key: avatar})

        # -------------------------
        # UID
        # -------------------------
        elif key == "uid":
            data[key] = cf.common_encode_one_value({key: uid})

        # -------------------------
        # BALANCE
        # -------------------------
        elif key == "balance":
            data[key] = cf.common_encode_one_value({key: 0})

        # -------------------------
        # BALANCE HISTORY
        # -------------------------
        elif key == "balance_history":
            data[key] = cf.common_encode_one_value(
                {
                    key: [
                        {
                            "id": "INIT-333",
                            "user_id": uid,
                            "type": "deposit",
                            "amount": 0,
                            "balance_before": 0,
                            "balance_after": 0,
                            "reference_id": "INIT-333",
                            "created_at": now,
                        }
                    ]
                }
            )

        # -------------------------
        # BUSINESS TAX
        # -------------------------
        elif key == "busines_tax":
            data[key] = cf.common_encode_one_value({key: False})

        # -------------------------
        # CREATED AT
        # -------------------------
        elif key == "created_at":
            data[key] = cf.common_encode_one_value({key: now})

        # -------------------------
        # DEPOSITS
        # -------------------------
        elif key == "deposits":
            data[key] = cf.common_encode_one_value(
                {
                    key: [
                        {
                            "id": "INIT-333",
                            "user_id": uid,
                            "type": "deposit",
                            "amount": 0,
                            "balance_before": 0,
                            "balance_after": 0,
                            "reference_id": "INIT-333",
                            "created_at": now,
                        }
                    ]
                }
            )

        # -------------------------
        # EMAIL
        # -------------------------
        elif key == "email":
            data[key] = cf.common_encode_one_value({key: data["email"]})

        # -------------------------
        # FAVORITE TEAMS
        # -------------------------
        elif key == "fav_teams":
            data[key] = cf.common_encode_one_value({key: []})

        # -------------------------
        # LAST STORE UPDATE
        # -------------------------
        elif key == "last_store_update":
            data[key] = cf.common_encode_one_value({key: now})

        # -------------------------
        # PUBLIC KEY (2FA)
        # -------------------------
        elif key == "public_key":
            data[key] = cf.common_encode_one_value(
                {key: cf.common_generate_2fa_secret()}
            )

        # -------------------------
        # REFERRAL ID
        # -------------------------
        elif key == "referral_id":
            data[key] = cf.common_encode_one_value({key: cf.common_generate_int_id(10)})

        # -------------------------
        # BOOLEAN STRING FIXES
        # -------------------------
        elif key in ["marketing_accepted"]:
            value = True if data[key] == "yes" else False
            data[key] = cf.common_encode_one_value({key: value})

        elif key in ["has_code"]:
            value = True if data[key] == "yes" else False
            data[key] = cf.common_encode_one_value({key: value})

        # -------------------------
        # PASSWORD
        # -------------------------
        elif key == "password":
            data[key] = cf.common_encode_one_value({key: data["password"]})

        # -------------------------
        # DEFAULT ENCODE
        # -------------------------
        else:
            data[key] = cf.common_encode_one_value({key: data[key]})

    record = cf.common_create_record("mam_users", data, id)
    return record


def get_account(data):
    """
    Retrieve minimal account information for authentication.

    This function fetches the user record from the `mam_users` store using the
    normalized email key. Only a minimal subset of fields is returned to the
    client for security reasons.

    Returned structure:
        {
            "fav_teams": <decoded fav_teams>,
            "saves": <decoded saves>,
            "email": <decoded email>,
            "token": <encoded dictionary>
        }

    Double-Encoding Behavior:
    -------------------------
    The `token` field is intentionally encoded twice.

    1. The `uid` stored in the database is already an encoded value
       produced by `cf.common_encode_one_value()`.

    2. A new dictionary `{email, token}` is created and encoded again
       using `cf.common_encode_dict()`.

    Purpose:
        - Prevent client-side manipulation of authentication data
        - Ensure payload integrity during transport
        - Allow the backend to verify both identity and session payload
        - Hide the raw UID structure from the client

    The frontend should treat `token` as an opaque authentication token
    and send it back to the API without attempting to decode it.

    Parameters
    ----------
    data : dict
        Expected to contain:
            - email : str

    Returns
    -------
    dict
        Safe payload containing the decoded email and a secure encoded token.
    """

    account = cf.common_get_record(
        "mam_users",
        cf.common_at_id(data["email"])
    )["data"]

    pprint (account)

    new_data = {}

    print (f"email in account -> {'email' in account}")
    decoded_email = cf.common_decode_one_value(account["email"])
    print (f"decoded email {decoded_email}")

    if "email" in account:
        new_data["email"] = cf.common_decode_one_value(account["email"])

    if "uid" in account:
        new_data["token"] = account["uid"]   # keep encrypted

    new_data_encoded = cf.common_encode_dict(new_data)

    to_sent = {
        "fav_teams" : cf.common_decode_one_value(account["fav_teams"]),
        "saves" : cf.common_decode_one_value(account["saves"]),
        "email": cf.common_decode_one_value(account["email"]),
        "token": new_data_encoded
    }

    return to_sent


# -------------------------------
# Route Map
# -------------------------------
routes = {
    "allPublic": all_public,
    "leaguesByCountry": leagues_by_country,
    "getTeamOfLeague": teams_of_league,
    "nextGames": next_games,
    "createAccount": create_account,
    "getAccount": get_account,
}


if __name__ == "__main__":

    pass

    data = {
        "account_id": "email with at instead of @",
        "account_verified": "no",
        "avatar": "https://ui-avatars.com/api/?name=Esteban+Jandres&background=F2C94C&color=fff&bold=true&rounded=true&format=svg",
        "balance": 0,
        "balance_history": ["wallet_transation"],
        "created_at": "millis",
        "deposits": ["wallet_transation"],
        "email": "esteban1@gmail.com",
        "fav_teams": [],
        "first_name": "Esteban Gilberto",
        "has_code": "no",
        "language": "es",
        "last_name": "Gutierrez Jandres",
        "last_store_update": "common_get_millis()",
        "last_store_update_counter": 0,
        "marketing_accepted": "yes",
        "password": "Mysuperpassword",
        "profile": "profile",
        "public_key": "cf.common_generate_2fa_secret()",
        "referred_by": "",
        "referral_id": "cf.common_generate_int_id()",
        "role": "user",
        "saves": [],
        "tax": "n/a",
        "uid": "40 digits id",
        "user_name": "",
        "verification_email_sent_count": "yes",
    }

    login_data = {"email": data["email"], "password": data["password"]}

    for target in routes:
        if target == "getAccount":

            # target = "leaguesByCountry"
            leagueId = 331
            teamId = 66

            handler = routes.get(target)
            if target == "createAccount":
                print(handler(data))

            elif target == "getAccount":
                pprint(handler(login_data))

            else:
                print(
                    handler({"update": target, "leagueId": leagueId, "teamId": teamId})
                )
    #         # api_leagues_by_country()
    #         # pprint (get_all_public_saves(False))
