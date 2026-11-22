"""Attendance model — mark and query attendance records."""
import sqlite3
from datetime import date, datetime, timedelta
from models import get_db


def check_already_marked_today(student_id):
    """
    Check if a student is already marked present today.
    Returns (already_marked: bool, record: dict or None).
    """
    today = date.today().isoformat()
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM attendance WHERE student_id = ? AND date = ?",
            (student_id, today)
        ).fetchone()
        if row:
            return True, dict(row)
        return False, None


def mark_attendance(student_id):
    """
    Mark attendance for a student today.
    [FIX M1] Uses INSERT OR IGNORE to handle race conditions atomically.
    Returns True if newly marked, False if already marked.
    """
    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M:%S")

    with get_db() as db:
        cursor = db.execute(
            "INSERT OR IGNORE INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, 'Present')",
            (student_id, today, now),
        )
        db.commit()
        return cursor.rowcount > 0


def get_attendance_by_date(target_date, class_id=None):
    """Get attendance records for a specific date, optionally filtered by class."""
    with get_db() as db:
        if class_id:
            return db.execute("""
                SELECT a.*, s.name, s.roll_no, c.class_name, c.section
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                WHERE a.date = ? AND s.class_id = ?
                ORDER BY c.class_name, s.roll_no
            """, (target_date, class_id)).fetchall()
        else:
            return db.execute("""
                SELECT a.*, s.name, s.roll_no, c.class_name, c.section
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                WHERE a.date = ?
                ORDER BY c.class_name, s.roll_no
            """, (target_date,)).fetchall()


def get_attendance_by_student(student_id, start_date=None, end_date=None):
    """Get attendance history for a specific student."""
    with get_db() as db:
        query = """
            SELECT a.*, s.name, s.roll_no
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.student_id = ?
        """
        params = [student_id]

        if start_date:
            query += " AND a.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND a.date <= ?"
            params.append(end_date)

        query += " ORDER BY a.date DESC"
        return db.execute(query, params).fetchall()


def get_today_summary(class_id=None):
    """Get today's attendance summary."""
    today = date.today().isoformat()

    with get_db() as db:
        if class_id:
            total = db.execute(
                "SELECT COUNT(*) as cnt FROM students WHERE class_id = ?", (class_id,)
            ).fetchone()["cnt"]
            present = db.execute("""
                SELECT COUNT(*) as cnt FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date = ? AND s.class_id = ?
            """, (today, class_id)).fetchone()["cnt"]
        else:
            total = db.execute("SELECT COUNT(*) as cnt FROM students").fetchone()["cnt"]
            present = db.execute(
                "SELECT COUNT(*) as cnt FROM attendance WHERE date = ?", (today,)
            ).fetchone()["cnt"]

    return {
        "total": total,
        "present": present,
        "absent": total - present,
        "percentage": round((present / total * 100), 1) if total > 0 else 0,
    }


def get_attendance_report(start_date, end_date, class_id=None):
    """Get detailed attendance report for a date range."""
    with get_db() as db:
        if class_id:
            return db.execute("""
                SELECT a.date, a.time, a.status, s.name, s.roll_no, c.class_name, c.section
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                WHERE a.date BETWEEN ? AND ? AND s.class_id = ?
                ORDER BY a.date, c.class_name, s.roll_no
            """, (start_date, end_date, class_id)).fetchall()
        else:
            return db.execute("""
                SELECT a.date, a.time, a.status, s.name, s.roll_no, c.class_name, c.section
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                WHERE a.date BETWEEN ? AND ?
                ORDER BY a.date, c.class_name, s.roll_no
            """, (start_date, end_date)).fetchall()


def get_student_attendance_percentage(student_id, start_date=None, end_date=None):
    """Calculate attendance percentage for a student."""
    with get_db() as db:
        params_total = []
        params_present = [student_id]

        query_total = "SELECT COUNT(DISTINCT date) as cnt FROM attendance WHERE 1=1"
        query_present = "SELECT COUNT(*) as cnt FROM attendance WHERE student_id = ?"

        if start_date:
            query_total += " AND date >= ?"
            query_present += " AND date >= ?"
            params_total.append(start_date)
            params_present.append(start_date)
        if end_date:
            query_total += " AND date <= ?"
            query_present += " AND date <= ?"
            params_total.append(end_date)
            params_present.append(end_date)

        total_days = db.execute(query_total, params_total).fetchone()["cnt"]
        present_days = db.execute(query_present, params_present).fetchone()["cnt"]

    if total_days == 0:
        return 0.0
    return round((present_days / total_days * 100), 1)


def get_weekly_trend():
    """Get attendance counts for the last 7 days."""
    with get_db() as db:
        today = date.today()
        trend = []
        for i in range(6, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            row = db.execute("SELECT COUNT(*) as cnt FROM attendance WHERE date = ?", (d,)).fetchone()
            trend.append({"date": d, "count": row["cnt"] if row else 0})
        return trend
