from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import datetime

app = Flask(__name__)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017")
db = client["webhooks_db"]
collection = db["webhooks"]

@app.route("/", methods=["GET"])
def index():
    return "<h1>Webhook Receiver Active</h1>"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if data:
        data["received_at"] = datetime.datetime.utcnow()
        collection.insert_one(data)
        return jsonify({"message": "Webhook received!", "status": "success"}), 200
    else:
        return jsonify({"message": "No data received", "status": "failed"}), 400

@app.route("/data", methods=["GET"])
def show_data():
    all_data = list(collection.find({}, {"_id": 0}))
    if not all_data:
        all_data = [{}]
    return render_template("index.html", data=all_data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
