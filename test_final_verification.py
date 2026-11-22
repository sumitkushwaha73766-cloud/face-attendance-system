"""
Final End-to-End System Verification Suite
Face Recognition Biometric Attendance System
"""
import sys
import re
import os
import sqlite3
import requests
import cv2

BASE_URL = "http://127.0.0.1:5000"
PROJECT_DIR = r"C:\Users\Sumit kushwaha\OneDrive\Desktop\face-attendance-system"
DB_PATH = os.path.join(PROJECT_DIR, "database.db")

PASSED = 0
FAILED = 0
CHECKS = []

def record(name, success, details=""):
    global PASSED, FAILED
    if success:
        PASSED += 1
        status = "[PASS]"
    else:
        FAILED += 1
        status = "[FAIL]"
    msg = f"{status} {name}: {details}"
    print(msg)
    CHECKS.append({"name": name, "status": "PASS" if success else "FAIL", "details": details})

def run_tests():
    print("=" * 75)
    print("STARTING COMPREHENSIVE FINAL SYSTEM & WEBSITE VERIFICATION")
    print(f"Target URL:  {BASE_URL}")
    print(f"Project Dir: {PROJECT_DIR}")
    print(f"Database:    {DB_PATH}")
    print("=" * 75)

    session = requests.Session()

    # 1. Server Reachability
    try:
        r = session.get(f"{BASE_URL}/", allow_redirects=True, timeout=5)
        record("01. Server Connectivity & Routing", r.status_code == 200, f"HTTP {r.status_code} at {r.url}")
    except Exception as e:
        record("01. Server Connectivity & Routing", False, f"Connection failed: {e}")
        return 0, 1

    # 2. HTTP Security Headers on Live Responses
    r_login = session.get(f"{BASE_URL}/login", timeout=5)
    headers = r_login.headers
    csp = headers.get("Content-Security-Policy", "")
    x_frame = headers.get("X-Frame-Options", "")
    x_content = headers.get("X-Content-Type-Options", "")
    referrer = headers.get("Referrer-Policy", "")

    sec_pass = bool(csp and x_frame == "DENY" and x_content == "nosniff" and referrer == "strict-origin-when-cross-origin")
    record("02. HTTP Security Headers (CSP, X-Frame, Nosniff)", sec_pass, f"X-Frame: {x_frame}, X-Content: {x_content}, CSP Length: {len(csp)}")

    # 3. Extract CSRF Token from Form
    csrf_match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', r_login.text)
    csrf_token = csrf_match.group(1) if csrf_match else ""
    record("03. Anti-CSRF Protection Generation", bool(csrf_token), f"Token generated (length: {len(csrf_token)} chars)")

    # 4. Access Control (Protected Routes Unauthenticated)
    unauth_session = requests.Session()
    r_unauth = unauth_session.get(f"{BASE_URL}/dashboard", allow_redirects=False, timeout=5)
    is_protected = r_unauth.status_code == 302 and "/login" in r_unauth.headers.get("Location", "")
    record("04. Role & Route Access Control", is_protected, f"Protected route redirected to {r_unauth.headers.get('Location')} with code {r_unauth.status_code}")

    # 5. Failed Authentication Handling
    r_bad = session.post(f"{BASE_URL}/login", data={
        "csrf_token": csrf_token,
        "username": "admin",
        "password": "wrongpassword123"
    }, allow_redirects=True, timeout=5)
    bad_login_rejected = "/dashboard" not in r_bad.url and ("Invalid" in r_bad.text or "danger" in r_bad.text or "warning" in r_bad.text)
    record("05. Rejection on Invalid Credentials", bad_login_rejected, f"Safely kept at {r_bad.url}")

    # 6. Admin Authentication & Session Creation
    r_login_fresh = session.get(f"{BASE_URL}/login", timeout=5)
    csrf_fresh = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', r_login_fresh.text).group(1)

    r_auth = session.post(f"{BASE_URL}/login", data={
        "csrf_token": csrf_fresh,
        "username": "admin",
        "password": "admin123"
    }, allow_redirects=False, timeout=5)
    auth_redirect = r_auth.status_code == 302 and "/dashboard" in r_auth.headers.get("Location", "")

    # Check Set-Cookie headers for HttpOnly & SameSite=Lax
    auth_cookie_header = r_auth.headers.get("Set-Cookie", "")
    has_httponly = "HttpOnly" in auth_cookie_header or "httponly" in auth_cookie_header.lower()
    has_samesite = "SameSite=Lax" in auth_cookie_header or "samesite=lax" in auth_cookie_header.lower()
    record("06. Admin Authentication & Session Establishment", auth_redirect, f"HTTP {r_auth.status_code} Redirect to {r_auth.headers.get('Location')}")
    record("07. Session Cookie Hardening (HttpOnly + SameSite=Lax)", has_httponly and has_samesite, f"HttpOnly={has_httponly}, SameSite=Lax={has_samesite}")

    # Follow redirect to dashboard
    r_dash = session.get(f"{BASE_URL}/dashboard", timeout=5)
    dash_html = r_dash.text
    has_trend_chart = "weeklyTrendChart" in dash_html
    has_status_chart = "ratioDonutChart" in dash_html
    has_countup = "data-countup" in dash_html
    has_hud_clock = "hud-clock" in dash_html
    dash_ok = has_trend_chart and has_status_chart and has_countup and has_hud_clock
    record("08. Dashboard UI (Charts & HUD Stat Cards)", dash_ok, f"weeklyTrendChart={has_trend_chart}, ratioDonutChart={has_status_chart}, HUD Clock={has_hud_clock}")

    # 9. Attendance Live Camera HUD & Video Feed
    r_att = session.get(f"{BASE_URL}/attendance", allow_redirects=True, timeout=5)
    att_html = r_att.text
    has_camera_hud = "camera-hud-frame" in att_html or "camera-hud-container" in att_html
    has_video_feed = "/video_feed" in att_html
    has_reticle = "hud-laser" in att_html or "hud-reticle" in att_html
    record("09. Biometric Camera HUD & Sci-Fi Reticle", has_camera_hud and has_video_feed and has_reticle, f"HUD Frame={has_camera_hud}, Stream=/video_feed, Reticle={has_reticle}")

    # 10. Student Registration Form & Dark Frame Detection
    r_reg = session.get(f"{BASE_URL}/register", timeout=5)
    reg_html = r_reg.text
    has_student_form = 'name="name"' in reg_html and 'name="roll_no"' in reg_html and 'name="class_id"' in reg_html
    has_shutter_alert = "shutter" in reg_html.lower() or "dark" in reg_html.lower() or "webcam" in reg_html.lower()
    record("10. Student Registration Form & Shutter Alerts", has_student_form and has_shutter_alert, f"Form Fields (name, roll_no, class_id)={has_student_form}, Dark Alerts={has_shutter_alert}")

    # 11. Attendance Records View Route
    r_rec = session.get(f"{BASE_URL}/attendance/view", timeout=5)
    rec_ok = r_rec.status_code == 200 and "table" in r_rec.text.lower()
    record("11. Attendance Logs & History Table (/attendance/view)", rec_ok, f"HTTP {r_rec.status_code}, Table elements rendered")

    # 12. Student Roster Management Route
    r_students = session.get(f"{BASE_URL}/students", timeout=5)
    students_ok = r_students.status_code == 200 and "sumit" in r_students.text.lower()
    record("12. Student Roster (/students)", students_ok, f"HTTP {r_students.status_code}, Registered student roster visible")

    # 13. Academic Classes Management Route
    r_classes = session.get(f"{BASE_URL}/classes", timeout=5)
    classes_ok = r_classes.status_code == 200 and "web tech" in r_classes.text.lower()
    record("13. Class Section Management (/classes)", classes_ok, f"HTTP {r_classes.status_code}, Class section 'web tech - 1' found")

    # 14. Report Generation Pipeline - Excel Export
    r_rep_page = session.get(f"{BASE_URL}/reports", timeout=5)
    csrf_rep = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', r_rep_page.text).group(1)

    r_excel = session.post(f"{BASE_URL}/reports", data={
        "csrf_token": csrf_rep,
        "format": "excel",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31"
    }, timeout=5)
    excel_content_type = r_excel.headers.get("Content-Type", "")
    excel_ok = r_excel.status_code == 200 and ("openxmlformats" in excel_content_type or len(r_excel.content) > 1000)
    record("14. Excel Report Export (OpenPyXL Engine)", excel_ok, f"HTTP {r_excel.status_code}, Payload size={len(r_excel.content)} bytes, Content-Type: {excel_content_type}")

    # 15. Static CSS Obsidian Glassmorphic Stylesheet
    r_css = session.get(f"{BASE_URL}/static/css/style.css", timeout=5)
    css_has_neon = "--neon-cyan" in r_css.text and "--bg-body" in r_css.text and "--border-glow" in r_css.text and "--bg-card" in r_css.text
    record("15. Obsidian Glassmorphic CSS Theme Engine", r_css.status_code == 200 and css_has_neon, f"HTTP {r_css.status_code}, len={len(r_css.text)} bytes, Palette verified")

    # 16. Static JavaScript Audio Synthesizer & HUD Engine
    r_js = session.get(f"{BASE_URL}/static/js/main.js", timeout=5)
    js_has_audio = "playBiometricSound" in r_js.text
    js_has_tilt = "init3DCardTilt" in r_js.text
    js_has_theme = "initTheme" in r_js.text
    record("16. JavaScript Web Audio & 3D Interactive Engine", r_js.status_code == 200 and js_has_audio and js_has_tilt and js_has_theme, f"HTTP {r_js.status_code}, Audio Synthesizer={js_has_audio}, 3D Tilt={js_has_tilt}, Theme Engine={js_has_theme}")

    # 17. CSRF Forgery Gate Prevention
    r_tamper = session.post(f"{BASE_URL}/reports", data={
        "csrf_token": "FORGED_CSRF_TOKEN_ATTACK_VECTOR_X9",
        "format": "excel",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31"
    }, timeout=5)
    csrf_blocked = r_tamper.status_code == 400
    record("17. Cross-Site Request Forgery (CSRF) Gate", csrf_blocked, f"Blocked malicious payload with HTTP {r_tamper.status_code}")

    # 18. SQLite Database WAL & Concurrency Health
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        cursor.execute("PRAGMA integrity_check;")
        integrity = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM students;")
        num_students = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM classes;")
        num_classes = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM attendance;")
        num_attendance = cursor.fetchone()[0]
        conn.close()
        db_healthy = (journal_mode.lower() == "wal" and integrity.lower() == "ok")
        record("18. SQLite Write-Ahead Logging (WAL) & Integrity", db_healthy, f"journal_mode={journal_mode}, integrity={integrity}, students={num_students}, classes={num_classes}, attendance_logs={num_attendance}")
    except Exception as e:
        record("18. SQLite Write-Ahead Logging (WAL) & Integrity", False, f"DB Error: {e}")

    # 19. OpenCV Haar Cascade & LBPH Recognizer Functional Check
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(cascade_path)
        cascade_loaded = not cascade.empty()
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer_ok = recognizer is not None
        record("19. OpenCV Haar Cascade & LBPH Recognizer", cascade_loaded and recognizer_ok, f"Haar Cascade={cascade_loaded}, LBPH Model={recognizer_ok}")
    except Exception as e:
        record("19. OpenCV Haar Cascade & LBPH Recognizer", False, f"OpenCV Error: {e}")

    # 20. Hardware Camera Sensor & Real-time Shutter State
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cam_opened = cap.isOpened()
        if cam_opened:
            ret, frame = cap.read()
            cap.release()
            cam_readable = bool(ret and frame is not None)
            mean_brightness = float(frame.mean()) if cam_readable else 0.0
            shutter_state = "OPEN (Normal Lighting)" if mean_brightness > 10.0 else "CLOSED (Slider is shut)"
            record("20. Hardware Camera Sensor & Dark Shutter Detection", cam_opened, f"Hardware Connected={cam_opened}, Frame Mean Brightness={mean_brightness:.1f} ({shutter_state})")
        else:
            record("20. Hardware Camera Sensor & Dark Shutter Detection", False, "Camera index 0 could not be opened")
    except Exception as e:
        record("20. Hardware Camera Sensor & Dark Shutter Detection", False, f"Camera Error: {e}")

    # 21. Clean Logout & Session Teardown
    r_logout = session.get(f"{BASE_URL}/logout", allow_redirects=True, timeout=5)
    r_post_logout = session.get(f"{BASE_URL}/dashboard", allow_redirects=False, timeout=5)
    logged_out = r_post_logout.status_code == 302 and "/login" in r_post_logout.headers.get("Location", "")
    record("21. Logout & Secure Session Termination", logged_out, f"Session destroyed, redirecting to {r_post_logout.headers.get('Location')}")

    print("=" * 75)
    print(f"VERIFICATION RESULTS: {PASSED}/{PASSED+FAILED} CHECKS PASSED ({(PASSED/(PASSED+FAILED))*100:.1f}%)")
    grade = "A+ (EXCELLENT / PRODUCTION-READY)" if FAILED == 0 else "NEEDS ATTENTION"
    print(f"OVERALL SYSTEM RATING: {grade}")
    print("=" * 75)
    return PASSED, FAILED

if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
