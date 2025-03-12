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

### **Backend API Routes** ###
# Route to Add a Room
@app.route("/add_room", methods=["POST"])
def add_room():
    data = request.json
    gender = data.get("gender")
    hostel = data.get("hostel")
    room_number = data.get("roomNumber")
    room_type = data.get("roomType")

    if not gender or not hostel or not room_number or not room_type:
        return jsonify({"error": "Missing details"}), 400

    if rooms_collection.find_one({"roomNumber": room_number, "hostel": hostel}):
        return jsonify({"error": "Room already exists in this hostel!"}), 409

    rooms_collection.insert_one({"gender": gender, "hostel": hostel, "roomNumber": room_number, "roomType": room_type})
    return jsonify({"message": f"Room {room_number} added successfully in {hostel}!"}), 201

# Route to Delete a Room
@app.route("/delete_room", methods=["DELETE"])
def delete_room():
    data = request.json
    room_number = data.get("roomNumber")

    if not room_number:
        return jsonify({"error": "Missing room number"}), 400

    result = rooms_collection.delete_one({"roomNumber": room_number})
    if result.deleted_count == 0:
        return jsonify({"error": "Room not found"}), 404

    return jsonify({"message": f"Room {room_number} deleted successfully!"}), 200

# Route to Allocate a Room and Store in MongoDB
@app.route('/allocate_room', methods=['POST'])
def allocate_room():
    data = request.json
    if not all(key in data for key in ["studentName", "usn", "roomType", "roomId"]):
        return jsonify({"error": "Missing fields"}), 400

    allocation = {
        "studentName": data["studentName"],
        "usn": data["usn"],
        "roomType": data["roomType"],
        "roomId": data["roomId"]
    }

    allocations_collection.insert_one(allocation)  # Store in MongoDB
    return jsonify({"message": f"Room {data['roomId']} allocated successfully for {data['studentName']}"}), 201

if __name__ == "__main__":
    app.run(debug=True)
