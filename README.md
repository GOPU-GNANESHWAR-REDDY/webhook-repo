# Webhook Repo for Techstax Assignment
# Flask Webhook Receiver

A Flask application to receive GitHub Webhooks and store relevant push and pull request events in MongoDB.

---

## 📌 Features

- ✅ Receives GitHub Webhooks for:
  - Push Events
  - Pull Request Events (Opened, Merged)
- ✅ Stores webhook data in MongoDB
- ✅ Logging of events and errors to `webhook_logs.log`
- ✅ API to fetch stored webhook data (`/data`)
- 🚧 Error handling & validation
- 🚧 Future improvements (see below)

---

## 🛠️ Tech Stack

- **Flask** (Python)
- **MongoDB Atlas**
- **PyMongo**
- **Dotenv**
- **Logging Module**

---

## 🏗️ Setup & Installation

1️⃣ Clone the repo:

```bash
git clone https://github.com/<your-username>/webhook-repo.git
cd webhook-repo

#Install dependencies
pip install -r requirements.txt

#Create a .env file in the root directory and add your MongoDB URI
MONGO_URI=your_mongo_connection_string

#Run the app
python app.py #App will run on http://localhost:5000/

## 👋 Contributors
- Gnaneshwar Gopu
