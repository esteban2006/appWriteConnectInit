import json
import sys
import os
import requests
import time
from pprint import pprint
from collections import defaultdict


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


# -------------------------------
# Route Update Map
# -------------------------------
update_maps = {
    "leaguesByCountry": {"day": 1},
    "allPublic": {"miminutesn": 5},
    "getTeamOfLeague": {"day": 1},
    "nextGames": {"day": 1},
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
def fetch(collection_id, document_id, update):
    record = cf.common_get_record(collection_id, document_id)

    today = record.get("data", {}).get("today")
    new_today = None
    millis = str(cf.common_get_millis())

    if today is not None and not cf.common_ensure_millis(today):
        new_today = millis
        print(f"today will now be {new_today}")

    else:
        requireds_update = cf.common_time_passed(int(today), update_maps[update])
        if requireds_update:
            pass

    if not record or "data" not in record:
        return ({"error": "Record not found"}, 404)

    return decode_record(record)


# -------------------------------
# Route Handlers
# -------------------------------
def leagues_by_country(data):
    return fetch(
        os.getenv("leages_by_country_collection_id"), "leaguesInCountry", data["update"]
    )


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

    # handler = routes.get("leaguesByCountry")
    # handler({"update": "leaguesByCountry"})
    api_leagues_by_country()
