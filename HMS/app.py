from flask import Flask, render_template, request, jsonify,session,flash, send_from_directory
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pymongo import MongoClient
from flask_cors import CORS
from bson.objectid import ObjectId
from flask import Flask, render_template, url_for, redirect
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText

app = Flask(__name__, template_folder="templates")  # Ensure Flask finds HTML files
CORS(app)

# MongoDB Configuration
client = MongoClient("mongodb://localhost:27017/")
db = client["user_db"]
rooms_collection = db["rooms"]
allocations_collection = db["roomallocation"]
notifications_collection = db["notifications"]
swap_requests_collection = db["swap_requests"]
users_collection = db["users"]  # Correct collection name
leave_requests_collection = db["leave_requests"]
attendance_collection = db["attendance"]
complanits_collection = db["complaint"]
# Room capacity constraints
ROOM_CAPACITY = {
    "2": 2,  # 2-sharing
    "3": 3,  # 3-sharing
    "8": 8   # 8-sharing
}
### **Frontend Routes (Render HTML Pages)** ###
@app.route('/')
def homepage():
    return render_template("homepage.html")
app.secret_key = 'your_secret_key'

# Dummy users (replace with MongoDB or SQL later)
users = {
    "admin": {"password": "adminpass", "role": "admin"},
    "student": {"password": "studentpass", "role": "student"}
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if role == 'admin':
            # Check admin credentials (replace with a secure database query)
            if username == 'admin' and password == 'admin123':  # Example credentials
                session['role'] = 'admin'
                session['username'] = username
                flash("Login successful!", "success")
                # return "Login successful"
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials!')
                # return "Invalid admin credentials"
                return redirect(url_for('login'))
        
        elif role == 'student':
            # Check student credentials in the database
            student = users_collection.find_one({'username': username})
            if student and check_password_hash(student['password'], password):  # Use check_password_hash
                session['role'] = 'student'
                session['username'] = username
                flash("Login successful!", "success")
                return redirect(url_for('student_dashboard'))  # Replace with the student dashboard route
            else:
                flash('Invalid student credentials!')
                return redirect(url_for('login'))
        
        else:
            flash('Please select a valid role.')
            return redirect(url_for('login'))

    return render_template('login.html')
    

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        contact_number = request.form['contact_number']
        age = request.form['age']
        gender = request.form['gender']
        email = request.form['email']
        dob = request.form['dob']
        address = request.form['address']
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        users_collection.insert_one({
            'student_id': student_id,
            'name': name,
            'contact_number': contact_number,
            'age': age,
            'gender': gender,
            'email': email,
            'dob': dob,
            'address': address,
            'username': username,
            'password': hashed_password
        })
        flash("Registration successful! Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/notification')
def notification():
    return render_template('notification.html')

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

# ✅ Logout Route (Redirects to Homepage)
@app.route('/logout')
def logout():
    return redirect(url_for('homepage'))

# @app.route('/notifications')
# def notifications():
#     return render_template("notification.html")

# Admin Dashboard Route
@app.route('/ladmin_dashboard')
def ladmin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    # Fetch all student data and leave requests
    students = list(users_collection.find({}))
    leave_requests = list(leave_requests_collection.find({}))

    # Debugging: print the leave requests data to see if it includes student_name
    print(leave_requests)

    return render_template('ladmin_dashboard.html', students=students, leave_requests=leave_requests)

# Student Dashboard Route
@app.route('/lstudent_dashboard')
def lstudent_dashboard():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    student = users_collection.find_one({'username': session['username']})
    if not student:
        flash("Student not found!")
        return redirect(url_for('login'))

    leave_requests = list(leave_requests_collection.find({'student_id': student['student_id']}))
    leave_count = len(leave_requests)

    return render_template('lstudent_dashboard.html', 
                           student=student, 
                           leave_requests=leave_requests, 
                           leave_count=leave_count)

# Leave Request Form Route
@app.route('/leave_request', methods=['GET', 'POST'])
def leave_request():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    student = users_collection.find_one({'username': session['username']})
    if not student:
        flash("Student not found!")
        return redirect(url_for('login'))

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        room_id = request.form.get('room_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason')

        # Fetch student's name
        student_name = student['name']

        # Debug: Print the form data
        print(f"Received data: student_id={student_id}, room_id={room_id}, start_date={start_date}, end_date={end_date}, reason={reason}, student_name={student_name}")

        if not all([student_id, room_id, start_date, end_date, reason]):
            flash("All fields are required!")
            return redirect(url_for('leave_request'))

        # Generate PDF filename
        pdf_filename = f"leave_request_{student_id}_{room_id}.pdf"
        pdf_path = os.path.join('static', pdf_filename)
        generate_leave_pdf(student_id, room_id, start_date, end_date, reason, pdf_path)

        # Insert the leave request into MongoDB with student name
        leave_requests_collection.insert_one({
            'student_id': student_id,
            'room_id': room_id,
            'start_date': start_date,
            'end_date': end_date,
            'reason': reason,
            'student_name': student_name,  # Added student name
            'pdf_filename': pdf_filename,
            'status': 'pending'  # Default status is pending
        })

        # Send email to admin
        send_leave_request_email(student_id, student_name, student['email'], pdf_path)

        flash("Leave request submitted successfully and email sent to admin!")
        return redirect(url_for('student_dashboard'))

    return render_template('leave_request.html', student_id=student['student_id'])


# Generate Leave Request PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# def generate_leave_pdf(student_id, room_id, start_date, end_date, reason, pdf_path):
#     try:
#         c = canvas.Canvas(pdf_path, pagesize=letter)
#         width, height = letter

#         # Title of the letter
#         c.setFont("Helvetica", 12)
#         c.drawString(100, height - 100, "Leave Request Letter")
#         c.line(100, height - 110, 500, height - 110)

#         # Letter content
#         c.drawString(100, height - 140, f"Student ID: {student_id}")
#         c.drawString(100, height - 160, f"Room ID: {room_id}")
#         c.drawString(100, height - 180, f"Leave Period: {start_date} to {end_date}")
#         c.drawString(100, height - 200, f"Reason for Leave: {reason}")
        
#         # Formal tone
#         c.drawString(100, height - 220, "Dear Sir/Madam,")
#         c.drawString(100, height - 240, "I am a student from SDMCET,")
#         c.drawString(100, height - 260, "asking you to please grant me leave for the following days.")
#         c.drawString(100, height - 280, "I hope you will approve this leave request.")
#         c.drawString(100, height - 300, "Thank you for your consideration.")
        
#         # Sign off
#         c.drawString(100, height - 320, "Sincerely,")
#         c.drawString(100, height - 340, f"Student ID: {student_id}")

#         # Save the PDF
#         c.save()

#     except Exception as e:
#         print(f"Error generating PDF: {e}")
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

def generate_leave_pdf(student_id, room_id, start_date, end_date, reason, pdf_path):
    try:
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        # Draw border
        margin = 30
        c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

        # Title
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width / 2, height - 80, "Leave Request Letter")

        # Auto-generate Date
        current_date = datetime.now().strftime("%d-%m-%Y")
        c.setFont("Helvetica", 12)
        c.drawRightString(width - 100, height - 120, f"Date: {current_date}")

        # Recipient Details
        c.drawString(100, height - 160, "To,")
        c.drawString(100, height - 180, "The Warden,")
        c.drawString(100, height - 200, "SDMCET Hostel,")
        c.drawString(100, height - 220, "Dharwad, Karnataka.")

        # Subject
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width / 2, height - 260, "Subject: Request for Leave")

        # Salutation
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 280, "Respected Sir/Madam,")

        # Letter Body
        text = (
            f"I am a student residing in Room {room_id} of the SDMCET Hostel. "
            f"My Student ID is {student_id}. "
            f"I kindly request leave from {start_date} to {end_date} "
            f"due to the following reason: {reason}. "
            "I assure you that I will abide by all hostel regulations and return on the mentioned date. "
            "I sincerely request you to consider my leave application and grant me permission."
        )

        c.setFont("Helvetica", 12)
        text_lines = []
        words = text.split(" ")
        line = ""
        max_width = width - 200
        
        for word in words:
            if c.stringWidth(line + word, "Helvetica", 12) < max_width:
                line += word + " "
            else:
                text_lines.append(line.strip())
                line = word + " "
        
        if line:
            text_lines.append(line.strip())
        
        y_position = height - 310
        for line in text_lines:
            c.drawString(100, y_position, line.ljust(int(max_width / 6)))
            y_position -= 20

        # Conclusion
        c.drawString(100, y_position - 20, "Thank you for your time and consideration.")

        # Signature
        c.drawString(100, y_position - 80, "Sincerely,")
        c.drawString(100, y_position - 100, f"{student_id}")

        # Save the PDF
        c.save()

    except Exception as e:
        print(f"Error generating PDF: {e}")

#send_leave_request
@app.route('/send_leave_request', methods=['GET', 'POST'])
def send_leave_request():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    student = users_collection.find_one({'username': session['username']})
    if not student:
        flash("Student not found!")
        return redirect(url_for('login'))

    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        if pdf_file and pdf_file.filename.endswith('.pdf'):
            pdf_path = os.path.join('static', pdf_file.filename)
            pdf_file.save(pdf_path)

            # Optionally send the PDF to the admin or update MongoDB
            flash("Leave request sent successfully!")
        else:
            flash("Invalid file format. Please upload a PDF.")

    return render_template('send_leave_request.html', student=student)


# Send email with attachment
def send_leave_request_email(student_id, name, email, pdf_path):
    try:
        from_email = "shostelmanagement@gmail.com"
        from_password = "System@123"
        to_email = "admin_email@example.com"

        subject = f"Leave Request from {name} (Student ID: {student_id})"
        body = f"Dear Admin,\n\n{name} (Student ID: {student_id}) has submitted a leave request. Please find the attached PDF.\n\nThank you."

        # Set up email
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF
        from email.mime.application import MIMEApplication

        with open(pdf_path, "rb") as attachment:
            part = MIMEApplication(attachment.read(), _subtype="pdf")
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_path))
            msg.attach(part)

        # Send email
        import smtplib
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")

    except Exception as e:
        print(f"Error sending email: {e}")

# Admin approval/rejection routes
from bson.objectid import ObjectId
from bson.errors import InvalidId

@app.route('/admin/approve_leave_request/<leave_id>', methods=['GET'])
def approve_leave_request(leave_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    try:
        leave_request = leave_requests_collection.find_one({'_id': ObjectId(leave_id)})
        if leave_request:
            leave_requests_collection.update_one({'_id': ObjectId(leave_id)}, {'$set': {'status': 'approved'}})
            flash("Leave request approved!")
        else:
            flash("Leave request not found.")
    except InvalidId:
        flash("Invalid leave request ID.")
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_leave_request/<leave_id>', methods=['GET'])
def reject_leave_request(leave_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    try:
        leave_request = leave_requests_collection.find_one({'_id': ObjectId(leave_id)})
        if leave_request:
            leave_requests_collection.update_one({'_id': ObjectId(leave_id)}, {'$set': {'status': 'rejected'}})
            flash("Leave request rejected.")
        else:
            flash("Leave request not found.")
    except InvalidId:
        flash("Invalid leave request ID.")
    
    return redirect(url_for('admin_dashboard'))


# Serve Static Files for PDFs
@app.route('/static/<filename>')
def serve_file(filename):
    return send_from_directory('static', filename)

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import secrets

# Forgot Password Route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = users_collection.find_one({'email': email})
        if user:
            token = secrets.token_urlsafe(16)
            users_collection.update_one({'email': email}, {'$set': {'reset_token': token}})
            reset_link = url_for('reset_password', token=token, _external=True)
            
            msg = Message("Password Reset Request", recipients=[email])
            msg.body = f"Click the link to reset your password: {reset_link}"
            mail.send(msg)
            flash("A password reset link has been sent to your email.")
        else:
            flash("Email not found.")
    return render_template('forgot_password.html', title="Forgot Password")

# Reset Password Route
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = users_collection.find_one({'reset_token': token})
    if not user:
        flash("Invalid or expired token.")
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        hashed_password = generate_password_hash(new_password)
        users_collection.update_one({'reset_token': token}, {'$set': {'password': hashed_password}, '$unset': {'reset_token': ""}})
        flash("Password reset successfully! Please log in.")
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', title="Reset Password")

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Example SMTP server, use your provider
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'shostelmanagement@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'System@123'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'shostelmanagement@gmail.com'

mail = Mail(app)

# Ensure the static folder exists
if not os.path.exists('static'):
    os.makedirs('static')

### **🔹 API: Admin Adds a Room**
@app.route("/add_room", methods=["POST"])
def add_room():
    data = request.json
    gender = data.get("gender")
    hostel = data.get("hostel")
    room_number = str(data.get("roomNumber"))
    room_type = str(data.get("roomType"))

    if not gender or not hostel or not room_number or not room_type:
        return jsonify({"error": "Missing details"}), 400

    if rooms_collection.find_one({"roomNumber": room_number, "hostel": hostel}):
        return jsonify({"error": "Room already exists in this hostel!"}), 409

    rooms_collection.insert_one({"gender": gender, "hostel": hostel, "roomNumber": room_number, "roomType": room_type})
    return jsonify({"message": f"Room {room_number} added successfully in {hostel}!"}), 201

#Get room type
@app.route('/get_room_types', methods=['GET'])
def get_room_types():
    hostel = request.args.get("hostel")

    if not hostel:
        return jsonify({"error": "Missing hostel parameter"}), 400

    # Fetch distinct room types for the selected hostel
    room_types = sorted(set(str(room["roomType"]) for room in rooms_collection.find(
        {"hostel": hostel},
        {"_id": 0, "roomType": 1}
    ) if "roomType" in room))

    if not room_types:
        return jsonify({"error": "No available room types for this hostel."}), 404

    return jsonify({"roomTypes": room_types})

### **🔹 API: Fetch Available Rooms**
@app.route('/get_available_rooms', methods=['GET'])
def get_available_rooms():
    hostel = request.args.get("hostel")
    room_type = str(request.args.get("roomType"))

    if not hostel or not room_type:
        return jsonify({"error": "Missing parameters"}), 400

    # Fetch all rooms of the requested type in the given hostel
    all_rooms = list(rooms_collection.find(
        {"roomType": room_type, "hostel": hostel},
        {"_id": 0, "roomNumber": 1}
    ))

    available_rooms = []
    for room in all_rooms:
        room_number = str(room["roomNumber"])
        allocated_students = allocations_collection.count_documents({"roomNumber": room_number})

        if allocated_students < ROOM_CAPACITY.get(room_type, 0):
            available_rooms.append(room_number)

    if not available_rooms:
        return jsonify({"error": "No available rooms"}), 404

    return jsonify({"rooms": available_rooms})

@app.route('/delete_room', methods=['POST'])
def delete_room():
    data = request.json
    print("Received delete request:", data)  # Debugging log

    # Ensure all required fields are present
    gender = data.get("gender")
    hostel = data.get("hostel")
    room_number = str(data.get("roomNumber"))
    room_type = str(data.get("roomType"))

    if not gender or not hostel or not room_number or not room_type:
        return jsonify({"error": "Missing details"}), 400

    # Find the room with matching details
    room = rooms_collection.find_one({
        "gender": gender, 
        "hostel": hostel, 
        "roomNumber": room_number, 
        "roomType": room_type
    })

    if not room:
        return jsonify({"error": "Room not found with the specified details"}), 404

    # Delete the room
    rooms_collection.delete_one({"_id": room["_id"]})

    # Print confirmation message
    print(f"Room {room_number} in {hostel} deleted successfully.")

    return jsonify({"message": f"Room {room_number} in {hostel} deleted successfully!"}), 200


### **🔹 API: Admin Allocates Student to a Room**
@app.route('/allocate_room', methods=['POST'])
def allocate_room():
    data = request.json
    student_name = data.get("studentName")
    usn = data.get("usn")
    gender = data.get("gender")
    hostel = data.get("hostel")
    room_type = str(data.get("roomType"))
    room_number = str(data.get("roomNumber"))

    if not all([student_name, usn, gender, hostel, room_type, room_number]):
        return jsonify({"error": "Missing fields"}), 400

    room = rooms_collection.find_one({"roomNumber": room_number, "hostel": hostel})
    if not room:
        return jsonify({"error": "Room does not exist"}), 400

    allocated_students = allocations_collection.count_documents({"roomNumber": room_number})
    if allocated_students >= ROOM_CAPACITY.get(room_type, 0):
        return jsonify({"error": "Room is full!"}), 400

    allocations_collection.insert_one({
        "studentName": student_name,
        "usn": usn,
        "gender": gender,
        "hostel": hostel,
        "roomType": room_type,
        "roomNumber": room_number
    })

    return jsonify({"message": f"Room {room_number} allocated successfully for {student_name}"}), 201

#swap rooms
### **🔹 API: Swap Rooms**
@app.route('/swap_rooms_request', methods=['POST'])
def swap_rooms_request():
    """Swaps rooms between two students if they exist."""
    data = request.json
    student1 = data.get("student1")
    student2 = data.get("student2")

    if not student1 or not student2:
        return jsonify({"error": "Missing student details"}), 400

    # Fetch students from the database
    student1_data = allocations_collection.find_one({"usn": student1["usn"], "roomNumber": student1["roomNumber"]})
    student2_data = allocations_collection.find_one({"usn": student2["usn"], "roomNumber": student2["roomNumber"]})

    if not student1_data:
        return jsonify({"error": f"Student {student1['name']} (USN: {student1['usn']}) not found in Room {student1['roomNumber']}"}), 404
    if not student2_data:
        return jsonify({"error": f"Student {student2['name']} (USN: {student2['usn']}) not found in Room {student2['roomNumber']}"}), 404

    # Swap room numbers
    allocations_collection.update_one(
        {"usn": student1["usn"]},
        {"$set": {"roomNumber": student2["roomNumber"]}}
    )
    allocations_collection.update_one(
        {"usn": student2["usn"]},
        {"$set": {"roomNumber": student1["roomNumber"]}}
    )

    # Store swap request for admin notification
    swap_requests_collection.insert_one({
        "student1": student1,
        "student2": student2,
        "status": "Pending Approval"
    })

    return jsonify({"message": f"Swap is successfully done for {student1['name']} and {student2['name']}.Thank you!"}), 200


@app.route('/get_allocations', methods=['GET'])
def get_allocations():
    """Fetches all allocated rooms from MongoDB."""
    allocations = list(allocations_collection.find({}, {"_id": 0, "studentName": 1, "usn": 1, "roomNumber": 1, "roomType": 1}))

    return jsonify(allocations)

### **Backend API Routes**
# ✅ Post Notification API
@app.route('/post_notification', methods=['POST'])
def post_notification():
    data = request.json
    notification_text = data.get("notification")

    if not notification_text:
        return jsonify({"error": "Notification text is required"}), 400

    new_notification = notifications_collection.insert_one({"message": notification_text})
    return jsonify({"message": "Notification posted successfully!", "id": str(new_notification.inserted_id)}), 201

# ✅ Fetch Notifications API
@app.route('/get_notifications', methods=['GET'])
def get_notifications():
    notifications = list(notifications_collection.find({}, {"_id": 1, "message": 1}))
    return jsonify([{"id": str(n["_id"]), "message": n["message"]} for n in notifications])

# ✅ Delete Notification API
@app.route('/delete_notification', methods=['DELETE'])
def delete_notification():
    data = request.json
    notification_id = data.get("id")

    if not notification_id:
        print("❌ No notification ID received.")  # Debugging Log
        return jsonify({"error": "Notification ID is required"}), 400

    try:
        print(f"🔹 Received ID to delete: {notification_id}")  # Debugging Log

        # ✅ Convert ID to ObjectId format
        if not ObjectId.is_valid(notification_id):
            print("❌ Invalid ObjectId format.")
            return jsonify({"error": "Invalid notification ID format"}), 400

        result = notifications_collection.delete_one({"_id": ObjectId(notification_id)})

        if result.deleted_count == 0:
            print("❌ Notification not found in MongoDB")
            return jsonify({"error": "Notification not found"}), 404

        print("✅ Notification deleted successfully")
        return jsonify({"message": "Notification deleted successfully"}), 200
    except Exception as e:
        print(f"❌ Error: {e}")  # Debugging Log
        return jsonify({"error": "Invalid notification ID"}), 400

import socket
import uuid
from datetime import datetime  # Import datetime for date tracking

# Your Mobile Hotspot SSID
HOSTEL_WIFI_SSID = "Smiti"

# Function to check if connected to WiFi
def is_connected_to_wifi():
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
        if local_ip.startswith(("192.168.", "10.", "172.")):
            return True
        return False
    except:
        return False

# Function to get MAC Address
def get_mac_address():
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xFF) for elements in range(0, 2*6, 8)][::-1])
        return mac
    except:
        return None

# Route for homepage
@app.route('/main_attendance')
def main_attendance():
    return render_template("main_attendance.html")

# Route to mark attendance
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    student_name = data.get("student_name")
    student_id = data.get("student_id")

    if not is_connected_to_wifi():
        return jsonify({"status": "error", "message": "Not connected to hostel WiFi"}), 403

    mac_address = get_mac_address()
    if not mac_address:
        return jsonify({"status": "error", "message": "MAC address not found"}), 400

    # Get today's date
    today_date = datetime.today().strftime('%Y-%m-%d')

    # Store attendance with date
    attendance_data = {
        "student_name": student_name,
        "student_id": student_id,
        "mac_address": mac_address,
        "date": today_date,  # Added date field
        "status": "Present"
    }
    attendance_collection.insert_one(attendance_data)

    return jsonify({"status": "success", "message": "Attendance marked!"})

# Admin panel to view attendance records
@app.route('/view_attendance')
def view_attendance():
    return render_template("view_attendance.html")

# API for fetching attendance records
@app.route('/view_attendance/attendance_record', methods=['GET'])
def get_attendance_records():
    records = list(attendance_collection.find({}, {"_id": 0}))
    return jsonify(records)

# ### **Backend API Routes**
# # ✅ Post complaint API
# @app.route('/post_complaint', methods=['POST'])
# def post_complaint():
#     data = request.json
#     complaint_text = data.get("complaint")

#     if not complaint_text:
#         return jsonify({"error": "complaint text is required"}), 400

#     new_complaint = complaints_collection.insert_one({"message": complaint_text})
#     return jsonify({"message": "complaint posted successfully!", "id": str(new_complaint.inserted_id)}), 201

# # ✅ Fetch complaint API
# @app.route('/get_complaints', methods=['GET'])
# def get_complaints():
#     complaints = list(complaints_collection.find({}, {"_id": 1, "message": 1}))
#     return jsonify([{"id": str(n["_id"]), "message": n["message"]} for n in complaints])

# # ✅ Delete complaint API
# @app.route('/delete_complaint', methods=['DELETE'])
# def delete_complaint():
#     data = request.json
#     complaint_id = data.get("id")

#     if not complaint_id:
#         print("❌ No complaint ID received.")  # Debugging Log
#         return jsonify({"error": "complaint ID is required"}), 400

#     try:
#         print(f"🔹 Received ID to delete: {complaint_id}")  # Debugging Log

#         # ✅ Convert ID to ObjectId format
#         if not ObjectId.is_valid(complaint_id):
#             print("❌ Invalid ObjectId format.")
#             return jsonify({"error": "Invalid complaint ID format"}), 400

#         result = complaints_collection.delete_one({"_id": ObjectId(complaint_id)})

#         if result.deleted_count == 0:
#             print("❌ complaint not found in MongoDB")
#             return jsonify({"error": "complaint not found"}), 404

#         print("✅ complaint deleted successfully")
#         return jsonify({"message": "complaint deleted successfully"}), 200
#     except Exception as e:
#         print(f"❌ Error: {e}")  # Debugging Log
#         return jsonify({"error": "Invalid complaint ID"}), 400

if __name__ == "__main__":
    app.run(debug=True)