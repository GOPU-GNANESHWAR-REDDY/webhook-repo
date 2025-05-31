import logging
from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    filename="webhook_logs.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Use MONGO_URI from environment variables
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    logging.error("MONGO_URI environment variable is missing")
    raise Exception("MONGO_URI environment variable is missing")

# Create a MongoDB client
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)

db = client["webhooks_db"]
collection = db["webhooks"]

@app.route("/", methods=["GET"])
def index():
    logging.info("Health check hit on root endpoint")
    return "<h1>Webhook Receiver Active</h1>"

@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    payload = request.json

    if not payload:
        logging.warning("No data received in webhook")
        return jsonify({"message": "No data received", "status": "failed"}), 400

    logging.info(f"Received {event} event with payload: {payload}")

    data = {}
    timestamp = datetime.now(timezone.utc).strftime("%d %B %Y - %I:%M %p UTC")

    try:
        # Payload Validation: Push Event
        if event == "push":
            if "pusher" not in payload or "name" not in payload["pusher"] or "ref" not in payload:
                logging.warning("Invalid push payload: missing pusher or ref")
                return jsonify({"message": "Invalid push payload: missing pusher or ref", "status": "failed"}), 400

            data = {
                "action": "push",
                "author": payload["pusher"]["name"],
                "to_branch": payload["ref"].split("/")[-1],
                "from_branch": None,
                "timestamp": timestamp
            }

        # Payload Validation: Pull Request Event
        elif event == "pull_request":
            pr = payload.get("pull_request", {})
            if not payload.get("action") or not pr.get("user") or not pr["user"].get("login") or not pr.get("head") or not pr.get("base"):
                logging.warning("Invalid pull_request payload: missing required fields")
                return jsonify({"message": "Invalid pull_request payload: missing required fields", "status": "failed"}), 400

            action = payload["action"]
            if action == "opened":
                data = {
                    "action": "pull_request",
                    "author": pr["user"]["login"],
                    "from_branch": pr["head"]["ref"],
                    "to_branch": pr["base"]["ref"],
                    "timestamp": timestamp
                }
            elif action == "closed" and pr.get("merged"):
                data = {
                    "action": "merge",
                    "author": pr["user"]["login"],
                    "from_branch": pr["head"]["ref"],
                    "to_branch": pr["base"]["ref"],
                    "timestamp": timestamp
                }
            else:
                logging.info("Pull request not relevant")
                return jsonify({"message": "Pull request not relevant", "status": "ignored"}), 200

        else:
            logging.info(f"Unhandled event type: {event}")
            return jsonify({"message": f"Unhandled event: {event}", "status": "ignored"}), 200

        # Save to MongoDB
        collection.insert_one(data)
        logging.info(f"Saved data to MongoDB: {data}")

        return jsonify({"message": "Webhook data saved", "status": "success"}), 200

    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return jsonify({"message": "Error processing webhook", "status": "failed"}), 500

@app.route("/data", methods=["GET"])
def get_data():
    try:
        all_data = list(collection.find({}, {"_id": 0}))
        logging.info("Fetched all data from MongoDB")
        return jsonify(all_data), 200
    except Exception as e:
        logging.error(f"Error fetching data: {str(e)}")
        return jsonify({"message": "Error fetching data", "status": "failed"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
