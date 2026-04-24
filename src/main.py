import json
from pprint import pprint
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common_functions as cf 


def main(context):
    context.log(f"Function executed with the following context:")
    context.log(f"\n\tReceived request method: {context.req.method}")
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

        print("\n\nresponse sending out ")
        pprint(response)
        return response
    
    if context.req.method == "GET":
        try:
            if data.get("update") == "leaguesByCountry":  # Add this if statement
                context.log("Attempting to get leaguesByCountry...")

                try:
                    leaguesByCountry = cf.common_get_record("6766ef78000d7daec880", "leaguesInCountry")["data"]["data"]
                    response = leaguesByCountry
                    return create_response(response)

                except Exception as e:
                    context.error(f"Error creating user: {e}")
                    import traceback

                    error_message = traceback.format_exc()
                    context.error(f"Traceback: {error_message}")
                    return create_response(
                        {"error": "Error creating user",
                            "details": str(e)}, 500
                    )

        except Exception as e:
            context.error(f"Error processing request: {e}")
            import traceback

            error_message = traceback.format_exc()
            context.error(f"Traceback: {error_message}")
            return create_response(
                {"error": "Error processing request", "details": str(e)}, 400
            )
