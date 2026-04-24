import json
from pprint import pprint
import sys
import os

# Ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common_functions as cf 

def main(context):
    context.log(f"Function executed with method: {context.req.method}")
    
    # 1. Parse body (handle string or dict)
    data = context.req.body
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            data = {}

    # Define common headers for CORS
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Content-Type": "application/json",
    }

    # 2. Support both GET and POST (your tester.py sends POST by default)
    if context.req.method in ["GET", "POST"]:
        try:
            if data.get("update") == "leaguesByCountry":
                context.log("Attempting to get leaguesByCountry...")

                try:
                    record = cf.common_get_record("6766ef78000d7daec880", "leaguesInCountry")
                    
                    if record and "data" in record:
                        # Extract the nested data your logic expects
                        response_data = record["data"]["data"]
                        return context.res.json(response_data, 200, headers)
                    else:
                        return context.res.json({"error": "Record not found"}, 404, headers)

                except Exception as e:
                    context.error(f"Error fetching record: {e}")
                    return context.res.json({"error": "Database error", "details": str(e)}, 500, headers)

        except Exception as e:
            context.error(f"Error processing request: {e}")
            return context.res.json({"error": "Bad request", "details": str(e)}, 400, headers)

    # 3. CRITICAL: Catch-all return to prevent the "Return statement missing" error
    # This runs if the method isn't GET/POST or the "update" key is missing
    return context.res.json({
        "message": "No valid action specified or unsupported method.",
        "received_method": context.req.method,
        "received_data": data
    }, 400, headers)