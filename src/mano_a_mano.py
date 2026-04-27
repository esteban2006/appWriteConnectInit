import json
import sys
import os
import requests
import time
import copy
from pprint import pprint
from collections import defaultdict
from datetime import datetime


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common_functions as cf

# -------------------------------
# Api football
# -------------------------------


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

    apiUrl = os.getenv("apiFootball")
    url = f"{apiUrl}leagues"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": os.getenv("football_api_key"),
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
        print (f"[EXECUTING FIXED ] Table -> {table}")
        record = cf.common_get_record("mam_public_all", "all_public_1")

        if not record:
            return {}

        data = record.get("data", {}).get("data")

        if isinstance(data, str):
            return json.loads(data)

        return data or {}

    else:
        table = "mam_public_saves"
        print (f"[EXECUTING FIXED ] Table {table}")
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


def get_teams_of_league(league_id, season):
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

    season = datetime.now().year - 1 if not season else season

    apiUrl = os.getenv("apiFootball")
    url = f"{apiUrl}teams"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": os.getenv("football_api_key"),
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
                sample = copy.deepcopy(
                    data["response"][0]
                )  # Deep copy to avoid modification issues
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
        "interval": {"minutes": 5},
        "cols_to_update": ["data", "today", "counter"],
        "updates": False,
    },
    "getTeamOfLeague": {
        "handler": "getTeamOfLeague",
        "kwargs": {},
        "interval": {"minutes": 5},
        "cols_to_update": ["data", "today", "counter"],
        "updates": True,
    },
    "all": {
        "handler": "api_all",
        "interval": None,
    },
}


def fetch(collection_id: str, document_id: str, update: str):
    """
    Fetches a record, decides whether it needs updating based on a job config,
    optionally runs a handler, and updates the database.
    """

    # Get the job configuration based on the "update" key
    job = jobs.get(update)

    # If no job exists for this update type, return an error
    if not job:
        return {"error": "Invalid update job"}, 400

    # Retrieve the record from the database
    record = cf.common_get_record(collection_id, document_id)

    # If record does not exist, return 404
    if not record:
        return {"error": "Record not found"}, 404

    # Current timestamp in milliseconds
    now = cf.common_get_millis()

    # Extract data section safely (default to empty dict if missing)
    data = record.get("data", {})

    # Last update timestamp stored in record
    today = data.get("today")

    # Counter used for tracking how many updates occurred
    counter = data.get("counter", 0)

    # Job-defined update interval (e.g. every X ms/mins)
    interval = job.get("interval")

    # Validate that stored timestamp is in a usable format (millis-safe check)
    is_millis = cf.common_ensure_millis(today)

    # Default assumption: we should update
    should_update = True

    # If we have a valid interval and valid timestamp, check if enough time passed
    if interval and today and is_millis:
        should_update = cf.common_time_passed(int(today), interval)

    # ------------------------------------------------------------
    # CACHE SHORT-CIRCUIT:
    # If update is not needed OR job is explicitly disabled,
    # return cached record without running handler
    # ------------------------------------------------------------
    if not should_update or job.get("updates") is False:
        print(
            f"[CACHE] {document_id} -> this function does updates {not job.get('updates')}"
        )
        return decode_record(record)

    # ------------------------------------------------------------
    # RUN JOB HANDLER:
    # Execute the function associated with this update job
    # ------------------------------------------------------------
    handler = job["handler"]  # function to execute
    args = job.get("args", ())  # positional arguments
    kwargs = job.get("kwargs", {})  # keyword arguments

    # Execute handler and get result
    result = handler(*args, **kwargs)

    # ------------------------------------------------------------
    # BUILD UPDATE PAYLOAD:
    # Determine which fields should be updated in the DB
    # ------------------------------------------------------------
    payload = {}
    cols = job.get("cols_to_update", [])

    for col in cols:

        # Update "data" field with serialized result
        if col == "data":
            payload["data"] = cf.common_dict_str(result)

        # Update timestamp to current time
        elif col == "today":
            payload["today"] = str(now)

        # Increment update counter
        elif col == "counter":
            payload["counter"] = counter + 1

    # ------------------------------------------------------------
    # APPLY UPDATE TO DATABASE:
    # Only update if there is something to write
    # ------------------------------------------------------------
    if payload:
        cf.common_update_record(collection_id, document_id, payload)

    print(f"[UPDATED] {document_id}")

    # Return fresh result from handler
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
    return fetch(
        os.getenv("get_teams_in_league_collection_id"),
        f"mam_league_{data['leagueId']}",
        data["update"],
    )


def next_games(data):
    return fetch(
        os.getenv("next_games_collection_id"),
        f"next_games_team_{data['teamId']}",
        data["update"],
    )


# -------------------------------
# Route Map
# -------------------------------
routes = {
    "leaguesByCountry": leagues_by_country,
    "allPublic": all_public,
    "getTeamOfLeague": teams_of_league,
    "nextGames": next_games,
}


if __name__ == "__main__":

    handler = routes.get("allPublic")
    pprint (handler({"update": "allPublic"}))
    # api_leagues_by_country()
    # pprint (get_all_public_saves(False))
