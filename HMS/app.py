from flask import Flask, request, jsonify
from flask_pymongo import PyMongo

app = Flask(__name__)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/admin/room"  # Change URI as needed
mongo = PyMongo(app)

# Route to allocate room and store data in MongoDB
@app.route('/allocate', methods=['POST'])
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

    mongo.db.allocations.insert_one(allocation)

    return jsonify({"message": "Room allocated successfully", "data": allocation})

# Route to fetch all allocated rooms
@app.route('/allocations', methods=['GET'])
def get_allocations():
    allocations = list(mongo.db.allocations.find({}, {"_id": 0}))  # Exclude MongoDB ObjectId
    return jsonify(allocations)

if __name__ == '__main__':
    app.run(debug=True)
