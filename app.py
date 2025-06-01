import logging
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import hmac
import hashlib

# Setup logging
logging.basicConfig(
    filename="webhook_logs.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")

# Load MongoDB URI
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    logging.error("MONGO_URI environment variable is missing")
    raise Exception("MONGO_URI environment variable is missing")

# Load GitHub Webhook Secret
GITHUB_SECRET = os.getenv("GITHUB_SECRET")
if not GITHUB_SECRET:
    logging.error("GITHUB_SECRET environment variable is missing")
    raise Exception("GITHUB_SECRET environment variable is missing")

# MongoDB connection
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client["webhooks_db"]
collection = db["webhooks"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    signature = request.headers.get('X-Hub-Signature-256')
    body = request.data

    # Verify signature
    if not signature:
        logging.warning("No X-Hub-Signature-256 header in request")
        return jsonify({"message": "Missing signature", "status": "failed"}), 400

    expected_signature = 'sha256=' + hmac.new(GITHUB_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        logging.warning("Invalid signature: Potentially malicious request")
        return jsonify({"message": "Invalid signature", "status": "failed"}), 403

    payload = request.get_json()
    if not payload:
        logging.warning("No data received in webhook")
        return jsonify({"message": "No data received", "status": "failed"}), 400

    logging.info(f"Received {event} event with payload: {payload}")

    data = {}
    timestamp = datetime.now(timezone.utc).strftime("%d %B %Y - %I:%M %p UTC")

    try:
        if event == "ping":
            logging.info("Received ping event from GitHub")
            return jsonify({"message": "Ping received", "status": "success"}), 200

        if event == "push":
            pusher = payload.get("pusher", {})
            ref = payload.get("ref")
            if not pusher.get("name") or not ref:
                logging.warning("Invalid push payload: missing pusher or ref")
                return jsonify({"message": "Invalid push payload: missing pusher or ref", "status": "failed"}), 400

            data = {
                "action": "push",
                "author": pusher["name"],
                "to_branch": ref.split("/")[-1],
                "from_branch": None,
                "timestamp": timestamp
            }

        elif event == "pull_request":
            pr = payload.get("pull_request", {})
            action = payload.get("action")
            if not action or not pr.get("user") or not pr.get("head") or not pr.get("base"):
                logging.warning("Invalid pull_request payload: missing required fields")
                return jsonify({"message": "Invalid pull_request payload", "status": "failed"}), 400

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
