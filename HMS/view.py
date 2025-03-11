from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["admin"]  # Use your MongoDB database
rooms_collection = db["rooms"]  # Collection to store room details

# Route to add a room
@app.route("/add_room", methods=["POST"])
def add_room():
    data = request.json
    room_number = data.get("roomNumber")
    room_type = data.get("roomType")

    if not room_number or not room_type:
        return jsonify({"error": "Missing room details"}), 400

    # Check if room already exists
    if rooms_collection.find_one({"roomNumber": room_number}):
        return jsonify({"error": "Room already exists!"}), 409

    # Insert room into MongoDB
    rooms_collection.insert_one({"roomNumber": room_number, "roomType": room_type})
    
    return jsonify({"message": f"Room {room_number} added successfully!"}), 201

# Route to delete a room
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

if __name__ == "__main__":
    app.run(debug=True)
