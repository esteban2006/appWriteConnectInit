import requests
import os
from dotenv import load_dotenv
from pprint import pprint
import json
load_dotenv()

def get_world_list():
    print("sending get_world_list via REST API")

    function_id = "69ea79a30000a5d7b4e4"
    url = f"https://cloud.appwrite.io/v1/functions/{function_id}/executions"
    
    # 1. You MUST include the API Key and Project ID
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": os.getenv("project_name"),
        # "X-Appwrite-Key": os.getenv("app_key"), # <--- THIS was missing
    }

    # 2. Appwrite expects the trigger data to be a string inside the "body" field
    # 3. We add "async": False so the API waits for the result and sends it back
    payload = {
        "body": json.dumps({
            "update": "leaguesByCountry",
            "key": "2KAAFF2WD5VWP6PUD8ULISSRN6ZAVA10EGFBO169V89A9A0XAG",
            "document_id": "UYRP5H7G7B9WDQVSSNT1J2J770OLCC4DAGGIMMW3F0PJDCRL8A",
            "collection": "3MMX72FR1K5EDNW7IR4JQ326VXKUMD455QGXY5L64NB3YQJ1LH",
            "public_key": "348EUM2DFNASJ$C$8RZEVHELLZJM1RYX34KU6WYPOJQLSNVAHK5I4B",
        }),
        "async": False 
    }

    # 4. Use POST, not GET
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print("Function Output:")
        # # The actual return from your main.py is in 'responseBody'
        # pprint(result.get("responseBody")) 
        print (result["responseBody"])



        # Create a clean list of dictionaries
        # final_list = []

        # for category, details in result[0]:
        #     # Add the category name into the dictionary
        #     details['category'] = category
        #     final_list.append(details)

        # # Result
        # print(final_list)
    else:
        print(f"Error {response.status_code}:")
        pprint(response.json())

get_world_list()