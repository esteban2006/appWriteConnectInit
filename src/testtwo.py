
import requests
from pprint import pprint

def get_world_list():
    print("sending get_world_list")

    url = "https://cloud.appwrite.io/v1/functions/69ea79a30000a5d7b4e4/executions"
    
    # You MUST include these headers for Appwrite to accept the request
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": "unit-333", # Get this from Appwrite Console
    }

    data = {
        "update": "leaguesByCountry",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "public_key": "348EUM2DFNASJ$C$8RZEVHELLZJM1RYX34KU6WYPOJQLSNVAHK5I4B",
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201 or response.status_code == 200:
        pprint(response.json())
    else:
        print(f"Error {response.status_code}:")
        pprint(response.json())

get_world_list()