"""
Face Recognition Biometric Attendance System
Main Flask Application — Security-Hardened
"""
import os
import re
import cv2
import time
import base64
import logging
import numpy as np
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, Response, jsonify, send_file,
)
from flask_wtf.csrf import CSRFProtect  # [FIX C2]
from werkzeug.utils import secure_filename  # [FIX H1]
from config import Config
from models import init_db, get_db
from models.admin import (
    create_admin, verify_admin, admin_exists,
    get_admin_by_id, change_password,
)
from models.student import (
    add_student, get_all_students, get_students_by_class,
    get_student_by_id, get_student_by_roll, update_student,
    delete_student, get_all_face_encodings, validate_student_input,
)
from models.attendance import (
    mark_attendance, get_attendance_by_date, get_today_summary,
    get_attendance_report, get_student_attendance_percentage,
)
from services.face_service import detect_and_encode_face, encode_face_from_frame, recognize_face
from services.camera_service import camera
from services.report_service import generate_excel_report, generate_pdf_report
from services.email_service import send_attendance_summary

# ─── Logging ─────────────────────────────────────────────────
# [FIX L4] Use logging instead of print for error messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── App Setup ───────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)
app.permanent_session_lifetime = timedelta(seconds=Config.PERMANENT_SESSION_LIFETIME)

# [FIX C2] Enable CSRF protection globally
csrf = CSRFProtect(app)

# [FIX L1] Security headers
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Initialize database on first run
init_db()

# Create default admin if none exists
if not admin_exists():
    create_admin("admin", "admin123", "admin@college.com", must_change=True)
    logger.info("Default admin created → username: admin, password: admin123")

# [FIX H2] In-memory login attempt tracking
login_attempts = {}  # {ip_address: {"count": int, "lockout_until": float}}


# ─── Helpers ─────────────────────────────────────────────────

def allowed_file(filename):
    """[FIX C3] Check if uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def is_login_locked(ip):
    """[FIX H2] Check if an IP is locked out from login attempts."""
    if ip in login_attempts:
        info = login_attempts[ip]
        if info.get("lockout_until", 0) > time.time():
            return True
        if info.get("lockout_until", 0) <= time.time() and info.get("count", 0) >= Config.MAX_LOGIN_ATTEMPTS:
            # Reset after lockout expires
            login_attempts[ip] = {"count": 0, "lockout_until": 0}
    return False


def record_failed_login(ip):
    """[FIX H2] Record a failed login attempt."""
    if ip not in login_attempts:
        login_attempts[ip] = {"count": 0, "lockout_until": 0}
    login_attempts[ip]["count"] += 1
    if login_attempts[ip]["count"] >= Config.MAX_LOGIN_ATTEMPTS:
        login_attempts[ip]["lockout_until"] = time.time() + Config.LOGIN_LOCKOUT_SECONDS
        logger.warning(f"Login locked for IP {ip} after {Config.MAX_LOGIN_ATTEMPTS} failed attempts")


def clear_login_attempts(ip):
    """Clear failed attempts on successful login."""
    login_attempts.pop(ip, None)


# ─── Auth Decorator ──────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        # [FIX M8] Re-validate admin exists in DB
        admin = get_admin_by_id(session["admin_id"])
        if not admin:
            session.clear()
            flash("Session expired. Please login again.", "warning")
            return redirect(url_for("login"))
        # [FIX H3] Force password change on first login
        if admin["must_change_password"] and request.endpoint != "change_password_page" and request.endpoint != "logout":
            flash("You must change your default password before continuing.", "warning")
            return redirect(url_for("change_password_page"))
        return f(*args, **kwargs)
    return decorated


# [FIX I2] Template context processor for current datetime
@app.context_processor
def inject_now():
    return {"now": datetime.now}


# ─── Helper: Get all classes ────────────────────────────────
def get_all_classes():
    with get_db() as db:
        return db.execute("SELECT * FROM classes ORDER BY class_name, section").fetchall()


# ─── Routes ──────────────────────────────────────────────────

# --- Auth ---
@app.route("/")
def index():
    if "admin_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ip = request.remote_addr

        # [FIX H2] Check lockout
        if is_login_locked(ip):
            remaining = int(login_attempts[ip]["lockout_until"] - time.time())
            flash(f"Too many failed attempts. Try again in {remaining // 60 + 1} minute(s).", "danger")
            return render_template("login.html")

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = verify_admin(username, password)

        if admin:
            clear_login_attempts(ip)
            session.permanent = True  # [FIX M6] Enable session expiry
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            record_failed_login(ip)
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


# [FIX H3] Password change route
@app.route("/change-password", methods=["GET", "POST"])
def change_password_page():
    if "admin_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
        else:
            success, msg = change_password(session["admin_id"], old_password, new_password)
            if success:
                flash(msg, "success")
                return redirect(url_for("dashboard"))
            else:
                flash(msg, "danger")

    return render_template("change_password.html")


# --- Dashboard ---
@app.route("/dashboard")
@login_required
def dashboard():
    summary = get_today_summary()
    today_attendance = get_attendance_by_date(date.today().isoformat())
    classes = get_all_classes()
    students = get_all_students()
    return render_template(
        "dashboard.html",
        summary=summary,
        today_attendance=today_attendance,
        classes=classes,
        total_students=len(students),
        total_classes=len(classes),
    )


# --- Student Registration ---
@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    # Release backend camera lock so the browser can access the webcam
    try:
        camera.stop()
    except Exception:
        pass

    classes = get_all_classes()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        class_id = request.form.get("class_id")

        if not all([name, roll_no, class_id]):
            flash("All fields are required.", "danger")
            return render_template("register.html", classes=classes)

        # [FIX M4] Validate student input
        is_valid, error_msg = validate_student_input(name, roll_no)
        if not is_valid:
            flash(error_msg, "danger")
            return render_template("register.html", classes=classes)

        # [FIX H1] Sanitize roll_no for filesystem safety
        safe_roll_no = secure_filename(roll_no)
        if not safe_roll_no:
            flash("Invalid roll number format.", "danger")
            return render_template("register.html", classes=classes)

        # Check duplicate roll number
        if get_student_by_roll(roll_no):
            flash(f"Student with roll number {roll_no} already exists.", "danger")
            return render_template("register.html", classes=classes)

        # Handle photo upload or webcam capture
        photo = request.files.get("photo")
        captured_data = request.form.get("captured_photo")
        filepath = os.path.join(Config.UPLOAD_FOLDER, f"{safe_roll_no}.jpg")

        if photo and photo.filename:
            # [FIX C3] Validate file extension
            if not allowed_file(photo.filename):
                flash("Only JPG, JPEG, and PNG files are allowed.", "danger")
                return render_template("register.html", classes=classes)
            photo.save(filepath)
        elif captured_data:
            # Base64 webcam capture
            try:
                img_data = captured_data.split(",")[1]
                img_bytes = base64.b64decode(img_data)
                # [FIX L3] Limit base64 data size (5 MB)
                if len(img_bytes) > 5 * 1024 * 1024:
                    flash("Captured photo is too large.", "danger")
                    return render_template("register.html", classes=classes)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
            except Exception:
                flash("Invalid photo data. Please try again.", "danger")
                return render_template("register.html", classes=classes)
        else:
            flash("Please upload a photo or capture one from webcam.", "danger")
            return render_template("register.html", classes=classes)

        # Detect and encode face
        encoding, error = detect_and_encode_face(filepath)
        if error:
            os.remove(filepath)
            flash(error, "danger")
            return render_template("register.html", classes=classes)

        # Save student
        relative_path = f"uploads/{safe_roll_no}.jpg"
        if add_student(name, roll_no, int(class_id), relative_path, encoding):
            flash(f"Student {name} ({roll_no}) registered successfully! ✅", "success")
            return redirect(url_for("students"))
        else:
            flash("Failed to register student. Please try again.", "danger")

    return render_template("register.html", classes=classes)


# --- Take Attendance ---
@app.route("/attendance")
@login_required
def attendance():
    classes = get_all_classes()
    return render_template("attendance.html", classes=classes)


@app.route("/video_feed")
@login_required
def video_feed():
    """Video streaming route for MJPEG."""
    return Response(
        camera.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/api/recognize", methods=["POST"])
@login_required
def api_recognize():
    """API endpoint: capture frame, recognize face, mark attendance."""
    success, frame = camera.get_frame()
    if not success:
        return jsonify({"status": "error", "message": "Physical camera unavailable. Please use Photo Attendance."})

    encoding, face_location, error = encode_face_from_frame(frame)
    if error:
        return jsonify({"status": "error", "message": error})

    known_faces = get_all_face_encodings()
    match = recognize_face(encoding, known_faces)

    if match:
        newly_marked = mark_attendance(match["id"])
        return jsonify({
            "status": "success",
            "name": match["name"],
            "roll_no": match["roll_no"],
            "confidence": match["confidence"],
            "newly_marked": newly_marked,
            "message": f"{'Attendance marked for' if newly_marked else 'Already marked for'} {match['name']}",
        })
    else:
        return jsonify({"status": "unknown", "message": "Face not recognized"})


@app.route("/api/recognize_photo", methods=["POST"])
@login_required
def api_recognize_photo():
    """API endpoint: recognize face from an uploaded photo or browser snapshot and mark attendance."""
    photo = request.files.get("photo")
    captured_data = request.form.get("captured_photo")

    frame = None
    if photo and photo.filename:
        file_bytes = np.frombuffer(photo.read(), np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    elif captured_data:
        try:
            img_data = captured_data.split(",")[1]
            img_bytes = base64.b64decode(img_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception:
            return jsonify({"status": "error", "message": "Invalid photo data."})

    if frame is None:
        return jsonify({"status": "error", "message": "Please choose or capture a photo."})

    encoding, face_location, error = encode_face_from_frame(frame)
    if error:
        return jsonify({"status": "error", "message": error})

    known_faces = get_all_face_encodings()
    match = recognize_face(encoding, known_faces)

    if match:
        newly_marked = mark_attendance(match["id"])
        return jsonify({
            "status": "success",
            "name": match["name"],
            "roll_no": match["roll_no"],
            "confidence": match["confidence"],
            "newly_marked": newly_marked,
            "message": f"{'Attendance marked for' if newly_marked else 'Already marked today for'} {match['name']}",
        })
    else:
        return jsonify({"status": "unknown", "message": "Face not recognized. Student may not be registered yet."})


@app.route("/api/stop_camera", methods=["POST"])
@login_required
def api_stop_camera():
    """Stop the camera feed."""
    camera.stop()
    return jsonify({"status": "ok"})


@app.route("/api/capture_frame", methods=["POST"])
@login_required
def api_capture_frame():
    """Captures a single frame directly from camera service or hardware."""
    try:
        frame = None
        # If camera service is active and streaming
        if camera.is_running():
            success, f = camera.get_frame()
            if success and f is not None:
                frame = f

        # If not active or failed, open hardware directly
        if frame is None:
            cap = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_ANY)
            if cap.isOpened():
                for _ in range(3):
                    ret, f = cap.read()
                cap.release()
                if ret and f is not None:
                    frame = f

        if frame is None:
            return jsonify({"status": "error", "message": "Camera unavailable. Please use Option B (Upload Photo)."})

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            return jsonify({"status": "error", "message": "Failed to encode photo."})

        b64_str = base64.b64encode(buffer).decode("utf-8")
        return jsonify({"status": "success", "image": f"data:image/jpeg;base64,{b64_str}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# --- View Attendance ---
@app.route("/attendance/view")
@login_required
def view_attendance():
    target_date = request.args.get("date", date.today().isoformat())
    class_id = request.args.get("class_id", "")

    records = get_attendance_by_date(target_date, class_id if class_id else None)
    classes = get_all_classes()

    return render_template(
        "view_attendance.html",
        records=records,
        classes=classes,
        selected_date=target_date,
        selected_class=class_id,
    )


# --- Manage Students ---
@app.route("/students")
@login_required
def students():
    all_students = get_all_students()
    classes = get_all_classes()
    return render_template("students.html", students=all_students, classes=classes)


@app.route("/students/edit/<int:student_id>", methods=["POST"])
@login_required
def edit_student(student_id):
    name = request.form.get("name", "").strip()
    roll_no = request.form.get("roll_no", "").strip()
    class_id = request.form.get("class_id")

    # [FIX M4] Validate input
    is_valid, error_msg = validate_student_input(name, roll_no)
    if not is_valid:
        flash(error_msg, "danger")
        return redirect(url_for("students"))

    if update_student(student_id, name, roll_no, int(class_id)):
        flash("Student updated successfully.", "success")
    else:
        flash("Failed to update student.", "danger")
    return redirect(url_for("students"))


@app.route("/students/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student_route(student_id):
    student = get_student_by_id(student_id)
    if student:
        # Delete photo file
        photo_path = os.path.join(app.static_folder, student["photo_path"])
        if os.path.exists(photo_path):
            os.remove(photo_path)
        delete_student(student_id)
        flash("Student deleted successfully.", "success")
    else:
        flash("Student not found.", "danger")
    return redirect(url_for("students"))


# --- Manage Classes ---
@app.route("/classes", methods=["GET", "POST"])
@login_required
def classes_page():
    if request.method == "POST":
        class_name = request.form.get("class_name", "").strip()
        section = request.form.get("section", "").strip().upper()

        if not all([class_name, section]):
            flash("Class name and section are required.", "danger")
        elif len(class_name) > 50 or len(section) > 10:
            flash("Class name or section too long.", "danger")
        else:
            with get_db() as db:
                try:
                    db.execute(
                        "INSERT INTO classes (class_name, section) VALUES (?, ?)",
                        (class_name, section),
                    )
                    db.commit()
                    flash(f"Class {class_name} - {section} added! ✅", "success")
                except Exception:
                    flash("This class-section combination already exists.", "danger")

    classes = get_all_classes()
    return render_template("classes.html", classes=classes)


@app.route("/classes/delete/<int:class_id>", methods=["POST"])
@login_required
def delete_class(class_id):
    with get_db() as db:
        db.execute("DELETE FROM classes WHERE id = ?", (class_id,))
        db.commit()
    flash("Class deleted.", "success")
    return redirect(url_for("classes_page"))


# --- Reports ---
@app.route("/reports", methods=["GET", "POST"])
@login_required
def reports():
    classes = get_all_classes()

    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        class_id = request.form.get("class_id", "")
        report_format = request.form.get("format", "excel")

        # Validate date inputs
        if not start_date or not end_date:
            flash("Start and end dates are required.", "danger")
            return render_template("reports.html", classes=classes)

        data = get_attendance_report(
            start_date, end_date, class_id if class_id else None
        )

        if not data:
            flash("No attendance records found for the selected criteria.", "warning")
            return render_template("reports.html", classes=classes)

        if report_format == "pdf":
            filepath = generate_pdf_report(data)
        else:
            filepath = generate_excel_report(data)

        # [FIX M7] Validate filepath is in temp directory
        filepath = os.path.realpath(filepath)
        return send_file(filepath, as_attachment=True)

    return render_template("reports.html", classes=classes)


@app.route("/api/send_summary_email", methods=["POST"])
@login_required
def api_send_summary():
    """Send today's attendance summary via email."""
    admin = get_admin_by_id(session["admin_id"])
    if not admin or not admin["email"]:
        return jsonify({"status": "error", "message": "Admin email not configured"})

    summary = get_today_summary()
    success = send_attendance_summary(admin["email"], summary)

    if success:
        return jsonify({"status": "ok", "message": "Summary email sent!"})
    return jsonify({"status": "error", "message": "Failed to send email. Check SMTP config."})


# ─── Run ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🎓 Face Recognition Attendance System")
    print("=" * 50)
    print(f"🌐 Open http://127.0.0.1:5000 in your browser")
    print(f"🔐 Default login → admin / admin123")
    print("=" * 50 + "\n")
    app.run(debug=Config.DEBUG, host="127.0.0.1", port=5000)  # [FIX H4] localhost only
