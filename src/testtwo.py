import json # Add this import
import requests
from pprint import pprint

def get_world_list():
    print("sending get_world_list")

    url = "https://cloud.appwrite.io/v1/functions/69ea79a30000a5d7b4e4/executions"
    
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": "unit-333", 
    }

    # This is the data your code NEEDS
    function_params = {
        "update": "leaguesByCountry",
        "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
        "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
        "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
        "public_key": "348EUM2DFNASJ$C$8RZEVHELLZJM1RYX34KU6WYPOJQLSNVAHK5I4B",
    }

    # This is the format the Appwrite API REQUIRES
    # We put our params into a key called "body" as a JSON string
    api_payload = {
        "body": json.dumps(function_params),
        "method": "POST",
        "path": "/"
    }

    response = requests.post(url, headers=headers, json=api_payload)
    
    if response.status_code in [200, 201]:
        execution_result = response.json()
        # Remember: The function result is a string in responseBody
        if 'responseBody' in execution_result:
            pprint(json.loads(execution_result['responseBody']))
    else:
        print(f"Error {response.status_code}:", response.text)

get_world_list()