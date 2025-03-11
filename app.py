from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__, template_folder="templates")  # Ensure Flask finds HTML files
CORS(app)

# MongoDB Configuration
client = MongoClient("mongodb://localhost:27017/")
db = client["user_db"]
rooms_collection = db["rooms"]
allocations_collection = db["roomallocation"]
notifications_collection = db["notifications"]

### **Frontend Routes (Render HTML Pages)** ###
@app.route('/')
def homepage():
    return render_template("homepage.html")

@app.route('/main')
def main_dashboard():
    return render_template("main.html")

@app.route('/allocate')
def allocate():
    return render_template("allocate.html")

@app.route('/view')
def view_rooms():
    return render_template("view.html")

@app.route('/swap')
def swap_rooms():
    return render_template("swap.html")

@app.route('/manage')
def manage_rooms():
    return render_template("managerooms.html")

@app.route('/notifications')
def notifications():
    return render_template("notification.html")

if __name__ == "__main__":
    app.run(debug=True)
