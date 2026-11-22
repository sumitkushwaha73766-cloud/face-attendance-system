"""Student model — CRUD operations for student records."""
import re
import numpy as np
from models import get_db


def validate_student_input(name, roll_no):
    """
    [FIX M4] Validate student name and roll number.
    Returns (is_valid, error_message).
    """
    if not name or len(name) < 2 or len(name) > 100:
        return False, "Name must be between 2 and 100 characters."
    if not re.match(r"^[A-Za-z\s\-'.]+$", name):
        return False, "Name can only contain letters, spaces, hyphens, apostrophes, and periods."
    if not roll_no or len(roll_no) > 20:
        return False, "Roll number must be 1-20 characters."
    if not re.match(r"^[A-Za-z0-9_\-]+$", roll_no):
        return False, "Roll number can only contain letters, digits, hyphens, and underscores."
    return True, ""


def add_student(name, roll_no, class_id, photo_path, face_encoding):
    """Register a new student with face encoding."""
    with get_db() as db:
        try:
            encoding_blob = face_encoding.tobytes()
            db.execute(
                "INSERT INTO students (name, roll_no, class_id, photo_path, face_encoding) VALUES (?, ?, ?, ?, ?)",
                (name, roll_no, class_id, photo_path, encoding_blob),
            )
            db.commit()
            return True
        except Exception:
            return False


def get_all_students():
    """Get all students with class info."""
    with get_db() as db:
        return db.execute("""
            SELECT s.*, c.class_name, c.section
            FROM students s
            JOIN classes c ON s.class_id = c.id
            ORDER BY c.class_name, c.section, s.roll_no
        """).fetchall()


def get_students_by_class(class_id):
    """Get students filtered by class."""
    with get_db() as db:
        return db.execute("""
            SELECT s.*, c.class_name, c.section
            FROM students s
            JOIN classes c ON s.class_id = c.id
            WHERE s.class_id = ?
            ORDER BY s.roll_no
        """, (class_id,)).fetchall()


def get_student_by_id(student_id):
    """Get a single student by ID."""
    with get_db() as db:
        return db.execute("""
            SELECT s.*, c.class_name, c.section
            FROM students s
            JOIN classes c ON s.class_id = c.id
            WHERE s.id = ?
        """, (student_id,)).fetchone()


def get_student_by_roll(roll_no):
    """Get student by roll number."""
    with get_db() as db:
        return db.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no,)).fetchone()


def update_student(student_id, name, roll_no, class_id):
    """Update student details (without changing face)."""
    with get_db() as db:
        try:
            db.execute(
                "UPDATE students SET name = ?, roll_no = ?, class_id = ? WHERE id = ?",
                (name, roll_no, class_id, student_id),
            )
            db.commit()
            return True
        except Exception:
            return False


def delete_student(student_id):
    """Delete a student record."""
    with get_db() as db:
        db.execute("DELETE FROM students WHERE id = ?", (student_id,))
        db.commit()


def get_all_face_encodings():
    """Load all face encodings from DB for recognition."""
    with get_db() as db:
        rows = db.execute("SELECT id, name, roll_no, face_encoding FROM students").fetchall()

    results = []
    for row in rows:
        blob = row["face_encoding"]
        if blob is None:
            continue
        blob_len = len(blob)
        if blob_len == 16384 * 4:
            # OpenCV LBPH histogram (16,384 float32 values)
            encoding = np.frombuffer(blob, dtype=np.float32)
        elif blob_len == 128 * 8:
            # dlib 128-d vector (float64)
            encoding = np.frombuffer(blob, dtype=np.float64)
        elif blob_len == 456 * 8:
            # Legacy 456-d vector (float64)
            encoding = np.frombuffer(blob, dtype=np.float64)
        else:
            try:
                encoding = np.frombuffer(blob, dtype=np.float32)
            except Exception:
                encoding = np.frombuffer(blob, dtype=np.float64)

        results.append({
            "id": row["id"],
            "name": row["name"],
            "roll_no": row["roll_no"],
            "encoding": encoding,
        })
    return results
