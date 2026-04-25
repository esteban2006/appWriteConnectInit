import requests
import os
from dotenv import load_dotenv
from pprint import pprint
import json

load_dotenv()
url = f"https://cloud.appwrite.io/v1/functions/69ea79a30000a5d7b4e4/executions"
# 1. You MUST include the API Key and Project ID
headers = {
    "Content-Type": "application/json",
    "X-Appwrite-Project": os.getenv("project_name"),
    # "X-Appwrite-Key": os.getenv("app_key"), # <--- THIS was missing
}


def get_world_list():
    print("sending get_world_list via REST API")
    payload = {
        "body": json.dumps(
            {
                "update": "leaguesByCountry",
                "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
                "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
                "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
                "public_key": "348EUM2DFNASJ$C$8RZEVHELLZJM1RYX34KU6WYPOJQLSNVAHK5I4B",
            }
        ),
        "async": False,
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        result = response.json()
        print(
            f"Function Output: \n\nFunction data type {type(result)} \n\nFunction inner data {type(result['responseBody'])}\n\n Raw data {response}"
        )

        print(result["responseBody"])
    else:
        print(f"Error {response.status_code}:")
        pprint(response.json())


# get_world_list()


def all_public():
    print("sending get_world_list via REST API")
    payload = {
        "body": json.dumps(
            {
                "update": "allPublic",
                "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
                "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
                "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
                "public_key": "348EUM2DFNASJ$C$8RZEVHELLZJM1RYX34KU6WYPOJQLSNVAHK5I4B",
            }
        ),
        "async": False,
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        result = response.json()
        print("Function Output:")
        print(result["responseBody"])
    else:
        print(f"Error {response.status_code}:")
        pprint(response.json())


# all_public()


def teams_in_league():
    print("sending teams_in_league via REST API")
    payload = {
        "body": json.dumps(
            {
                "update": "getTeamOfLeague",
                "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
                "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
                "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
                "public_key": "348EUM2DFNASJ$C$8RZEVHELLZJM1RYX34KU6WYPOJQLSNVAHK5I4B",
                "leagueId": 10,
                "year": 2024,
            }
        ),
        "async": False,
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        result = response.json()
        pprint(result)
        print(
            f"Function Output: \n\nFunction data type {type(result)} \n\n"
            "Function inner data {type(result['responseBody'])}\n\n Raw data {response}"
        )
        print(result["responseBody"])
    else:
        print(f"Error {response.status_code}:")
        pprint(response.json())


teams_in_league()
