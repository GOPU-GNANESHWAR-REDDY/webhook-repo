from flask import Flask, request, jsonify
from pymongo import MongoClient
import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client["webhooks_db"]
collection = db["webhooks"]

@app.route("/", methods=["GET"])
def index():
    return "<h1>Webhook Receiver Active</h1>"

@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    payload = request.json

    if not payload:
        return jsonify({"message": "No data received", "status": "failed"}), 400

    data = {}
    timestamp = datetime.datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")

    if event == "push":
        data = {
            "action": "push",
            "author": payload["pusher"]["name"],
            "to_branch": payload["ref"].split("/")[-1],
            "from_branch": None,
            "timestamp": timestamp
        }

    elif event == "pull_request":
        action = payload["action"]
        if action == "opened":
            data = {
                "action": "pull_request",
                "author": payload["pull_request"]["user"]["login"],
                "from_branch": payload["pull_request"]["head"]["ref"],
                "to_branch": payload["pull_request"]["base"]["ref"],
                "timestamp": timestamp
            }
        elif action == "closed" and payload["pull_request"]["merged"]:
            data = {
                "action": "merge",
                "author": payload["pull_request"]["user"]["login"],
                "from_branch": payload["pull_request"]["head"]["ref"],
                "to_branch": payload["pull_request"]["base"]["ref"],
                "timestamp": timestamp
            }
        else:
            return jsonify({"message": "Pull request not relevant", "status": "ignored"}), 200

    else:
        return jsonify({"message": f"Unhandled event: {event}", "status": "ignored"}), 200

    collection.insert_one(data)
    print(f"Saved to DB: {data}")

    return jsonify({"message": "Webhook data saved", "status": "success"}), 200

@app.route("/data", methods=["GET"])
def get_data():
    all_data = list(collection.find({}, {"_id": 0}))
    return jsonify(all_data), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
