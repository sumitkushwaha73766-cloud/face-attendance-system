"""
Unit and integration tests for Face Recognition Attendance System.
"""
import os
import unittest
import tempfile
import sqlite3
import numpy as np

# Configure environment before imports
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["FLASK_DEBUG"] = "false"

from config import Config
from models import init_db, get_db
from models.admin import create_admin, verify_admin, change_password, get_admin_by_id
from models.student import (
    validate_student_input, add_student, get_all_students,
    get_student_by_roll, update_student, delete_student, get_all_face_encodings
)
from models.attendance import (
    mark_attendance, get_today_summary, get_attendance_by_date
)
from app import app


class TestFaceAttendanceSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary database for testing
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix=".db")
        Config.DATABASE_PATH = cls.db_path
        init_db()

    @classmethod
    def tearDownClass(cls):
        os.close(cls.db_fd)
        if os.path.exists(cls.db_path):
            try:
                os.remove(cls.db_path)
            except PermissionError:
                pass

    def test_01_student_input_validation(self):
        """Test input validation for student registration."""
        # Valid cases
        valid, msg = validate_student_input("John Doe", "CSE001")
        self.assertTrue(valid)

        # Invalid name (special characters / script tag)
        valid, msg = validate_student_input("<script>alert(1)</script>", "CSE002")
        self.assertFalse(valid)

        # Invalid roll number (path traversal attempts)
        valid, msg = validate_student_input("Alice", "../../secret")
        self.assertFalse(valid)

        # Empty name
        valid, msg = validate_student_input("", "CSE003")
        self.assertFalse(valid)

    def test_02_admin_auth_and_password_change(self):
        """Test admin creation, authentication and password policies."""
        created = create_admin("testadmin", "OldPass123", "test@college.com")
        self.assertTrue(created)

        # Verify login
        admin = verify_admin("testadmin", "OldPass123")
        self.assertIsNotNone(admin)

        # Wrong password
        bad_admin = verify_admin("testadmin", "WrongPass")
        self.assertIsNone(bad_admin)

        # Change password - weak password (fails)
        success, msg = change_password(admin["id"], "OldPass123", "weak")
        self.assertFalse(success)

        # Change password - strong password (succeeds)
        success, msg = change_password(admin["id"], "OldPass123", "NewSecret123")
        self.assertTrue(success)

        # Verify new password
        admin_new = verify_admin("testadmin", "NewSecret123")
        self.assertIsNotNone(admin_new)

    def test_03_student_and_attendance_workflow(self):
        """Test adding class, student, and marking attendance idempotently."""
        with get_db() as db:
            cursor = db.execute("INSERT INTO classes (class_name, section) VALUES ('BTech-CSE', 'A')")
            class_id = cursor.lastrowid
            db.commit()

        # Add dummy student
        fake_encoding = np.zeros(128, dtype=np.float64)
        added = add_student("Sumit Kushwaha", "2024CSE01", class_id, "uploads/2024CSE01.jpg", fake_encoding)
        self.assertTrue(added)

        student = get_student_by_roll("2024CSE01")
        self.assertIsNotNone(student)
        self.assertEqual(student["name"], "Sumit Kushwaha")

        # Mark attendance 1st time
        marked_first = mark_attendance(student["id"])
        self.assertTrue(marked_first)

        # Mark attendance 2nd time on the same day -> must return False (idempotent / no duplicate)
        marked_second = mark_attendance(student["id"])
        self.assertFalse(marked_second)

        # Verify summary
        summary = get_today_summary(class_id)
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["present"], 1)
        self.assertEqual(summary["absent"], 0)

    def test_04_flask_routes_protection(self):
        """Test that unauthenticated requests to protected routes redirect to login."""
        tester = app.test_client(self)

        # Protected dashboard route
        resp = tester.get("/dashboard")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

        # Protected attendance route
        resp = tester.get("/attendance")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])


if __name__ == "__main__":
    unittest.main()
