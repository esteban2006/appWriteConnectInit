import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import mano_a_mano as mam


# -------------------------------
# Response Helper
# -------------------------------
def response(data, status=200):
    return {
        "status": status,
        "body": json.dumps(data),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Content-Type": "application/json",
        },
    }


# -------------------------------
# Main Function
# -------------------------------
def main(context):

    context.log(f"Function executed with method: {context.req.method}")

    if context.req.method not in ["GET", "POST"]:
        return response({"error": "Method not allowed"}, 405)

    data = mam.parse_body(context.req.body)
    update = data.get("update", "no")

    if update not in mam.routes:
        return response({"error": "Update not available at this time"}, 405)

    # -------------------------------
    # Working with mano a mano only
    # -------------------------------

    if update in mam.routes:

        try:

            handler = mam.routes.get(update)

            if not handler:
                return response({"error": "Invalid update parameter"}, 400)

            to_sent = handler(data)
            print (f"response sending out: {to_sent} ")
            return response(to_sent)
        

        except Exception as e:

            context.error(str(e))

            return response(
                {"error": "Internal server error", "details": str(e)},
                500,
            )


if __name__ == "__main__":
    pass
