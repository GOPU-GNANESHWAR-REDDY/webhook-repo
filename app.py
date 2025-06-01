import logging
from flask import Flask, request, jsonify
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

app = Flask(__name__)

# Use MONGO_URI from environment variables
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    logging.error("MONGO_URI environment variable is missing")
    raise Exception("MONGO_URI environment variable is missing")

GITHUB_SECRET = os.getenv("GITHUB_SECRET")
if not GITHUB_SECRET:
    logging.error("GITHUB_SECRET environment variable is missing")
    raise Exception("GITHUB_SECRET environment variable is missing")

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
    signature = request.headers.get('X-Hub-Signature-256')
    body = request.data

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
        # ... (rest of your existing code remains the same)
        # Validations and MongoDB insert go here

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
