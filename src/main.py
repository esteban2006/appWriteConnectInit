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
    

    # 2. Support both GET and POST (your tester.py sends POST by default)

    if context.req.method in ["GET", "POST"]:
        try:
            if data.get("update") == "leaguesByCountry":
                context.log("Attempting to get leaguesByCountry...")

                try:
                    record = cf.common_get_record("6766ef78000d7daec880", "leaguesInCountry")
                    
                    if record and "data" in record:
                        # 1. Get the double-encoded string
                        response_data = record["data"]["data"]
                        
                        try:
                            # 2. First decode: Removes the outer escaped quotes 
                            # Result: "[[ \"National Teams\", ...]]" (now a valid JSON string)
                            first_decode = json.loads(response_data)
                            
                            # 3. Second decode: Converts that string into a real Python List
                            # Result: [['National Teams', {...}], ...]
                            final_json_data = json.loads(first_decode)
                            
                            return create_response(final_json_data, 200)
                        
                        except (json.JSONDecodeError, TypeError) as decode_error:
                            context.error(f"Decoding failed: {decode_error}")
                            # Fallback: If it's not double-encoded after all, try returning the original
                            return create_response(response_data, 200)

                    else:
                        return create_response({"error": "Record not found"}, 404)

                except Exception as e:
                    context.error(f"Error fetching record: {e}")
                    return create_response({"error": "Database error", "details": str(e)}, 500)

        except Exception as e:
            context.error(f"Error processing request: {e}")
            return create_response({"error": "Bad request", "details": str(e)}, 400)

    # 3. CRITICAL: Catch-all return to prevent the "Return statement missing" error
    # This runs if the method isn't GET/POST or the "update" key is missing
    return create_response({
        "message": "No valid action specified or unsupported method.",
        "received_method": context.req.method,
        "received_data": data
    }, 400)