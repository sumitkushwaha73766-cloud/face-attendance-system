# 🎓 Face Recognition Biometric Attendance System

A web-based attendance system that uses **face recognition** to automatically identify students and mark attendance in real-time.

## ✨ Features

- 📸 **Live Face Recognition** — Real-time webcam-based attendance
- 👤 **Student Registration** — Register with photo capture or upload
- 📊 **Admin Dashboard** — Attendance stats at a glance
- 📥 **Export Reports** — Download as Excel or PDF
- 📧 **Email Notifications** — Attendance summary alerts
- 🏫 **Multi-class Support** — Manage multiple classes and sections

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Face Recognition:** OpenCV, face_recognition (dlib)
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript, Bootstrap 5
- **Reports:** openpyxl (Excel), fpdf2 (PDF)

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Webcam

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/face-attendance-system.git
cd face-attendance-system

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

### 5. Open in browser
```
http://127.0.0.1:5000
```

### Default Login
- **Username:** `admin`
- **Password:** `admin123`

## 📁 Project Structure

```
face-attendance-system/
├── app.py                  # Flask application
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── models/                 # Database models
│   ├── admin.py
│   ├── student.py
│   └── attendance.py
├── services/               # Business logic
│   ├── face_service.py     # Face detection & recognition
│   ├── camera_service.py   # Webcam management
│   ├── report_service.py   # Excel/PDF generation
│   └── email_service.py    # Email notifications
├── templates/              # HTML templates
└── static/                 # CSS, JS, uploads
```

## 📸 How It Works

1. **Register Students** — Capture face via webcam or upload photo
2. **Start Attendance** — System detects faces from live camera feed
3. **Auto-Mark** — Recognized students get attendance marked automatically
4. **View & Export** — Check records and download reports

## 👨‍💻 Author

**Sumit Kushwaha** — B.Tech 3rd Year

## 📄 License

This project is for educational purposes (Mini Project).
