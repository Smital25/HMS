
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
from flask import Flask, render_template, request, redirect, url_for, flash, session
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash


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
complaints_collection = db["complaint"]



# Room capacity constraints
ROOM_CAPACITY = {
    "2": 2,  # 2-sharing
    "3": 3,  # 3-sharing
    "8": 8   # 8-sharing
}

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

app.secret_key = 'your_secret_key_here'
serializer = URLSafeTimedSerializer(app.secret_key)

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
            # Check admin credentials
            if username == 'admin' and password == 'admin123':
                session['role'] = 'admin'
                session['username'] = username
                flash("Login successful!", "success")
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials!')
                return redirect(url_for('login'))
        
        elif role == 'student':
            # Check student credentials
            student = users_collection.find_one({'username': username})
            if student and check_password_hash(student['password'], password):
                session['role'] = 'student'
                session['username'] = username
                session['student_id'] = student['student_id']  # Save student ID in session
                flash("Login successful!", "success")
                print(f"Session after login: {session}")  # Debugging line
                return redirect(url_for('student_dashboard'))  # Redirect to student dashboard
            else:
                flash('Invalid student credentials!')
                return redirect(url_for('login'))
        
        else:
            flash('Please select a valid role.')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_simple():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        
        user = users_collection.find_one({'username': username})
        if user:
            hashed_password = generate_password_hash(new_password)
            users_collection.update_one({'username': username}, {'$set': {'password': hashed_password}})
            flash('Password reset successfully. You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('reset_password_simple'))
    
    return render_template('forgot.html')

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

        # ✅ Check if username already exists
        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            flash("Username already taken! Please choose another.", "danger")
            return redirect(url_for('register'))

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
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/student_info')
def student_info():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    students = list(users_collection.find())  # Fetch all users
    return render_template('students_info.html', students=students)

@app.route('/student_dashboard')
def student_dashboard():
   student = users_collection.find_one({'username': session['username']})
   return render_template('student_dashboard.html', 
                           student=student)
                           
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/notification')
def notification():
    return render_template('notification.html')

@app.route('/main')
def main_dashboard():
    return render_template("main.html")

@app.route('/view')
def view_rooms():
    return render_template("view.html")

# @app.route('/swaps')
# def swap_rooms():
#     return render_template("swap.html")
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

#

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

#---------------
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import socket
import uuid

from datetime import datetime

def get_current_datetime():
    now = datetime.now()
    date_str = now.strftime("%d-%m-%Y")  
    time_str = now.strftime("%H:%M:%S")  
    return date_str, time_str

import subprocess

HOSTEL_WIFI_SSID = "Smiti"

def is_connected_to_wifi():
    try:
        output = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True)
        for line in output.splitlines():
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":")[1].strip()
                print(f"[DEBUG] Connected SSID: {ssid}")
                return ssid == HOSTEL_WIFI_SSID
        return False
    except Exception as e:
        print(f"WiFi check error: {e}")
        return False

HOSTEL_WIFI_PREFIX = "Smiti"  # Prefix of your hostel WiFi subnet

def is_connected_to_hostel_wifi():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return ip.startswith(HOSTEL_WIFI_PREFIX)
    except:
        return False

def get_mac_address():
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])
        return mac
    except:
        return None

# Function to get Current Date and Time
def get_current_datetime():
    now = datetime.now()
    # Format the date to 'DD-MM-YYYY'
    date_str = now.strftime("%d-%m-%Y")  # Format: DD-MM-YYYY
    
    # Format the time to 12-hour format with AM/PM
    time_str = now.strftime("%I:%M %p")  # Format: HH:MM AM/PM
    return date_str, time_str

from datetime import datetime, time

def is_within_allowed_time():
    now = datetime.now().time()
    start_time = time(21, 0)   # 9:00 PM
    end_time = time(22, 30)    # 10:30 PM

    return start_time <= now <= end_time

@app.route('/main_attendance')
def main_attendance():
    return render_template("main_attendance.html")

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    # Ensure student is logged in
    if 'role' not in session or session['role'] != 'student':
        return jsonify({"status": "error", "message": "Unauthorized. Please login as student."}), 401

    student_name = session.get('username')  # Get from session
    student_id = session.get('student_id')  # Get from session

    if not student_name or not student_id:
        return jsonify({"status": "error", "message": "Missing student session info. Please log in again."}), 400

    # ✅ TIME CHECK: Only allow between 9:00 PM and 10:30 PM
    if not is_within_allowed_time():
        return jsonify({
            "status": "error",
            "message": "Attendance can only be marked between 9:00 PM and 10:30 PM."
        }), 403

    # ✅ WiFi CHECK
    if not is_connected_to_wifi():
        return jsonify({"status": "error", "message": "You must be connected to hostel WiFi to mark attendance."}), 403

    # ✅ Get MAC Address
    mac_address = get_mac_address()
    if not mac_address:
        return jsonify({"status": "error", "message": "Unable to retrieve MAC address."}), 500

    # ✅ Get Date and Time
    date_str, time_str = get_current_datetime()

    # ✅ Prevent Duplicate
    existing = attendance_collection.find_one({
        "student_id": student_id,
        "date": date_str
    })
    if existing:
        return jsonify({"status": "error", "message": "Attendance already marked for today."}), 409

    # ✅ Insert Attendance
    attendance_data = {
        "student_name": student_name,
        "student_id": student_id,
        "mac_address": mac_address,
        "date": date_str,
        "time": time_str,
        "status": "Present"
    }

    attendance_collection.insert_one(attendance_data)
    return jsonify({"status": "success", "message": "Attendance marked successfully."})


@app.route('/view_attendance')
def view_attendance():
    return render_template("view_attendance.html")

@app.route('/view_attendance/attendance_record', methods=['GET'])
def get_attendance_records():
    records = list(attendance_collection.find({}, {"_id": 0}))
    return jsonify(records)

@app.route('/get_logged_in_student')
def get_logged_in_student():
    if 'role' not in session or session['role'] != 'student':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    student_name = session.get('username')
    student_id = session.get('student_id')  # Ensure this is set at login

    return jsonify({
        "status": "success",
        "student_name": student_name,
        "student_id": student_id
    })

# Route to render the report generation page
@app.route('/generate_report', methods=['GET'])
def generate_report():
    return render_template("generate_report.html")

# API to fetch report data by date range
@app.route('/generate_report/data', methods=['POST'])
def generate_report_data():
    data = request.json
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if not start_date_str or not end_date_str:
        return jsonify({"status": "error", "message": "Start and end dates are required."}), 400

    try:
        # Parse dates to datetime objects (assuming DD-MM-YYYY format)
        start_date = datetime.strptime(start_date_str, "%d-%m-%Y")
        end_date = datetime.strptime(end_date_str, "%d-%m-%Y")

        # Format to string for querying since DB stores as "DD-MM-YYYY"
        start_str = start_date.strftime("%d-%m-%Y")
        end_str = end_date.strftime("%d-%m-%Y")

        # Query records between the date range
        records = list(attendance_collection.find({
            "date": {"$gte": start_str, "$lte": end_str}
        }, {"_id": 0}))

        return jsonify({"status": "success", "records": records})
    
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date format. Use DD-MM-YYYY."}), 400
    
from flask import request, send_file, jsonify
from fpdf import FPDF
import io
from datetime import datetime

from flask import send_file, jsonify, request
from datetime import datetime
from fpdf import FPDF
import io

@app.route('/generate_report/pdf', methods=['POST'])
def generate_pdf_report():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not start_date or not end_date:
        return jsonify({"status": "error", "message": "Start and end dates are required."}), 400

    try:
        start = datetime.strptime(start_date, "%d-%m-%Y")
        end = datetime.strptime(end_date, "%d-%m-%Y")
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date format. Use DD-MM-YYYY."}), 400

    start_str = start.strftime("%d-%m-%Y")
    end_str = end.strftime("%d-%m-%Y")

    records = list(attendance_collection.find({
        "date": {"$gte": start_str, "$lte": end_str}
    }))

    if not records:
        return jsonify({"status": "error", "message": "No records found for selected dates."}), 404

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Attendance Report", ln=True, align='C')
    pdf.ln(10)

    # Set up table headers
    pdf.set_font("Arial", 'B', 10)
    col_widths = [40, 25, 30, 30, 30]  # Adjust widths as needed

    headers = ['Student Name', 'Student ID', 'Date', 'Time', 'Status']
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
    pdf.ln()

    # Table rows
    pdf.set_font("Arial", '', 10)
    for r in records:
        row = [
            r.get('student_name', 'N/A'),
            r.get('student_id', 'N/A'),
            r.get('date', 'N/A'),
            r.get('time', 'N/A'),
            r.get('status', 'N/A')
        ]
        for i, item in enumerate(row):
            pdf.cell(col_widths[i], 10, str(item), 1, 0, 'C')
        pdf.ln()

    # Write to memory and send
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_stream = io.BytesIO(pdf_bytes)
    pdf_stream.seek(0)

    return send_file(
        pdf_stream,
        mimetype='application/pdf',
        download_name='Attendance_Report.pdf',
        as_attachment=True
    )


# complaints_collection = []

@app.route('/student_complaint', methods=['GET', 'POST'])
def submit_complaint():
    if request.method == 'POST':
        try:
            # Get the JSON data from the request
            data = request.get_json()

            # Extract complaint details
            title = data.get('title')
            category = data.get('category')
            description = data.get('description')

            # Basic validation
            if not title or not category or not description:
                return jsonify({'success': False, 'message': 'Missing fields'}), 400

            # Get the current date and day
            current_datetime = datetime.now()
            date_str = current_datetime.strftime("%Y-%m-%d")
            day_str = current_datetime.strftime("%A")

            # Get student ID (assuming it's stored in session)
            student_id = session.get('student_id', 'Unknown')

            # Create complaint object
            complaint = {
                'title': title,
                'category': category,
                'description': description,
                'date': date_str,
                'day': day_str,
                'student_id': student_id
            }

            # Insert complaint into the MongoDB collection
            complaints_collection.insert_one(complaint)

            # Return success response
            return jsonify({'success': True, 'message': 'Complaint submitted successfully'})

        except Exception as e:
            # Log the detailed error message
            print(f"Error while submitting complaint: {e}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    # Serve the complaint form when the request method is GET
    return render_template('student_complaint.html')

@app.route('/admin_complaint', methods=['GET'])
def admin_complaint():
    try:
        # Fetch all complaints from the database
        complaints = list(complaints_collection.find())  # Convert cursor to list

        # Check if complaints are returned
        if complaints:
            return render_template('admin_complaint.html', complaints=complaints)
        else:
            return "No complaints found", 404
    except Exception as e:
        # Log the full exception message
        print(f"Error while fetching complaints: {e}")
        return f"Error fetching complaints: {e}", 500

@app.route('/delete_complaint/<complaint_id>', methods=['DELETE'])
def delete_complaint(complaint_id):
    try:
        # Validate the ObjectId format from the URL parameter
        if not ObjectId.is_valid(complaint_id):
            return jsonify({'success': False, 'message': 'Invalid complaint ID format'}), 400
        
        # Convert complaint_id to ObjectId
        object_id = ObjectId(complaint_id)
        print(f"Attempting to delete complaint with ObjectId: {object_id}")

        # Query for the complaint in the database
        complaint = db.complaints_collection.find_one({'_id': object_id})
        
        if not complaint:
            print(f"Complaint with ObjectId {object_id} not found.")
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404

        # Proceed with deletion if the complaint exists
        result = db.complaints_collection.delete_one({'_id': object_id})

        if result.deleted_count == 1:
            print(f"Complaint with ObjectId {object_id} deleted successfully.")
            return jsonify({'success': True, 'message': 'Complaint deleted successfully'})
        else:
            print(f"Failed to delete complaint with ObjectId {object_id}.")
            return jsonify({'success': False, 'message': 'Failed to delete complaint'}), 500

    except Exception as e:
        # Log and return the error message
        print(f"Error while deleting complaint: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500



#------------------ add rooms
# Endpoint: Add a new room
@app.route("/add_room", methods=["POST"])
def add_room():
    data = request.get_json()
    gender = data.get("gender")
    hostel = data.get("hostel")
    room_number = data.get("roomNumber")
    room_type = int(data.get("roomType"))  # 2/3/8 sharing

    if not (gender and hostel and room_number and room_type):
        return jsonify({"message": "Missing fields"}), 400

    # Check for existing room
    existing = rooms_collection.find_one({
        "room_number": room_number,
        "hostel": hostel,
        "sharing": room_type
    })

    if existing:
        return jsonify({"message": "Room already exists"}), 400

    room_doc = {
        "gender": gender,
        "hostel": hostel,
        "room_number": room_number,
        "sharing": room_type,
        "students": []
    }

    rooms_collection.insert_one(room_doc)
    return jsonify({"message": f"Room {room_number} added successfully in {hostel}."}), 200


# Endpoint: Delete a room
@app.route("/delete_room", methods=["POST"])
def delete_room():
    data = request.get_json()
    gender = data.get("gender")
    hostel = data.get("hostel")
    room_number = data.get("roomNumber")
    room_type = int(data.get("roomType"))

    if not (gender and hostel and room_number and room_type):
        return jsonify({"error": "Missing fields"}), 400

    query = {
        "room_number": room_number,
        "hostel": hostel,
        "sharing": room_type,
        "gender": gender
    }

    result = rooms_collection.delete_one(query)

    if result.deleted_count == 1:
        return jsonify({"message": "Room deleted successfully"}), 200
    else:
        return jsonify({"error": "Room not found"}), 404
#------------------------------------
@app.route('/manage')
def manage():
    return render_template("managerooms.html")

@app.route('/allocate')
def allocate():
    return render_template("allocate.html")


@app.route("/get_rooms", methods=["GET"])
def get_rooms():
    hostel = request.args.get("hostel")
    sharing = int(request.args.get("sharing"))

    rooms = list(rooms_collection.find({"hostel": hostel, "sharing": sharing}, {"_id": 0}))
    return jsonify({"rooms": rooms})


@app.route("/allocate_room", methods=["POST"])
def allocate_room():
    data = request.get_json()
    room_number = data.get("room_number")
    usn = data.get("student_id")

    if not room_number or not usn:
        return jsonify({"message": "Missing room number or student ID"}), 400

    # ✅ 1. Check if student is registered
    registered_student = users_collection.find_one({"student_id": usn})
    if not registered_student:
        return jsonify({"message": "Student is not registered. Allocation denied."}), 403

    # ✅ 2. Check if student is already allocated in any room
    existing_allocation = rooms_collection.find_one({"students.usn": usn})
    if existing_allocation:
        return jsonify({"message": f"Student is already allocated in room {existing_allocation['room_number']}."}), 409

    # ✅ 3. Fetch the target room
    room = rooms_collection.find_one({"room_number": room_number})
    if not room:
        return jsonify({"message": "Room not found"}), 404

    # ✅ 4. Check room capacity
    if len(room["students"]) >= room["sharing"]:
        return jsonify({"message": "Room is full"}), 400

    # ✅ 5. Get name from registered user
    name = registered_student["name"]

    # ✅ 6. Allocate the student
    rooms_collection.update_one(
        {"room_number": room_number},
        {"$push": {"students": {"name": name, "usn": usn}}}
    )

    allocations_collection.insert_one({
        "room_number": room_number,
        "name": name,
        "usn": usn,
        "hostel": room.get("hostel"),
        "sharing": room.get("sharing")
    })

    return jsonify({"message": "Student allocated successfully"}), 200


@app.route("/remove_student", methods=["POST"])
def remove_student():
    data = request.get_json()
    usn = data["usn"]
    room_number = data["room_number"]
    hostel = data["hostel"]

    result = rooms_collection.update_one(
        {"room_number": room_number, "hostel": hostel},
        {"$pull": {"students": {"usn": usn}}}
    )

    if result.modified_count > 0:
        allocations_collection.delete_many({"usn": usn})
        return jsonify({"message": "Student removed successfully"}), 200

    return jsonify({"message": "Student not found"}), 404


#--------------------------------------------------------------------
@app.route("/swap_rooms_request", methods=["POST"])
def swap_rooms_request():
    data = request.get_json()
    s1 = data.get("student1")
    s2 = data.get("student2")

    if not s1 or not s2:
        return jsonify({"error": "Missing student data"}), 400

    usn1, usn2 = s1["usn"], s2["usn"]
    room1, hostel1 = s1["roomNumber"], s1["hostel"]
    room2, hostel2 = s2["roomNumber"], s2["hostel"]
    gender1, gender2 = s1["gender"], s2["gender"]

    # ✅ Check same gender
    if gender1 != gender2:
        return jsonify({"error": "Swap allowed only between same gender"}), 403

    # ✅ Check hostel gender restriction
    male_hostels = {"Shamala", "Netravati", "Narmada"}
    female_hostels = {"Sharavati", "Hemavati"}

    if gender1 == "Male" and (hostel1 not in male_hostels or hostel2 not in male_hostels):
        return jsonify({"error": "Invalid male hostel selection."}), 400
    if gender1 == "Female" and (hostel1 not in female_hostels or hostel2 not in female_hostels):
        return jsonify({"error": "Invalid female hostel selection."}), 400

    # ✅ Check registration
    if not users_collection.find_one({"student_id": usn1}) or not users_collection.find_one({"student_id": usn2}):
        return jsonify({"error": "One or both students are not registered."}), 403

    # ✅ Fetch rooms based on room number + hostel
    room_doc_1 = rooms_collection.find_one({"room_number": room1, "hostel": hostel1})
    room_doc_2 = rooms_collection.find_one({"room_number": room2, "hostel": hostel2})

    if not room_doc_1 or not room_doc_2:
        return jsonify({"error": "One or both rooms not found."}), 404

    # ✅ Check students in correct rooms
    student_in_room_1 = next((s for s in room_doc_1["students"] if s["usn"] == usn1), None)
    student_in_room_2 = next((s for s in room_doc_2["students"] if s["usn"] == usn2), None)

    if not student_in_room_1 or not student_in_room_2:
        return jsonify({"error": "One or both students not found in claimed rooms."}), 400

    # ✅ Perform swap
    # Remove and push swapped students
    rooms_collection.update_one(
        {"room_number": room1, "hostel": hostel1},
        {"$pull": {"students": {"usn": usn1}}}
    )
    rooms_collection.update_one(
        {"room_number": room2, "hostel": hostel2},
        {"$pull": {"students": {"usn": usn2}}}
    )
    rooms_collection.update_one(
        {"room_number": room1, "hostel": hostel1},
        {"$push": {"students": student_in_room_2}}
    )
    rooms_collection.update_one(
        {"room_number": room2, "hostel": hostel2},
        {"$push": {"students": student_in_room_1}}
    )

    # ✅ Update allocation records
    allocations_collection.update_one(
        {"usn": usn1},
        {"$set": {"room_number": room2, "hostel": hostel2}}, upsert=True
    )
    allocations_collection.update_one(
        {"usn": usn2},
        {"$set": {"room_number": room1, "hostel": hostel1}}, upsert=True
    )

    return jsonify({"message": f"Room swap between {usn1} and {usn2} successful."}), 200
#---------------------------------------------------------------------------------------------
@app.route("/get_allocations", methods=["GET"])
def get_allocations():
    allocations = list(allocations_collection.find({}))
    result = []
    for alloc in allocations:
        result.append({
            "studentName": alloc.get("name", ""),              # <- name must be present
            "usn": alloc.get("usn", ""),                        # <- usn must be present
            "roomNumber": alloc.get("room_number", ""),         # <- must be string or int
            "roomType": str(alloc.get("sharing", "")),          # <- this was possibly missing
        })
    return jsonify(result), 200


@app.route("/delete_allocation", methods=["POST"])
def delete_allocation():
    data = request.get_json()
    usn = data.get("usn")
    room_number = data.get("roomNumber")

    if not usn or not room_number:
        return jsonify({"error": "Missing USN or room number"}), 400

    # Step 1: Find the allocation to get hostel
    allocation = allocations_collection.find_one({"usn": usn, "room_number": room_number})
    if not allocation:
        return jsonify({"error": "Allocation not found"}), 404

    hostel = allocation.get("hostel")
    if not hostel:
        return jsonify({"error": "Hostel info missing in allocation record"}), 500

    # Step 2: Remove student from the room
    result = rooms_collection.update_one(
        {"room_number": room_number, "hostel": hostel},
        {"$pull": {"students": {"usn": usn}}}
    )

    # Step 3: Delete from allocations
    allocations_collection.delete_one({"usn": usn})

    return jsonify({"message": f"Student {usn} removed from room {room_number}."}), 200





if __name__ == '__main__':
    app.run(debug=True)
