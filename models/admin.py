"""Admin model — authentication and user management."""
import re
from werkzeug.security import generate_password_hash, check_password_hash
from models import get_db


def create_admin(username, password, email="", must_change=True):
    """Create a new admin user."""
    with get_db() as db:
        try:
            db.execute(
                "INSERT INTO admin (username, password_hash, email, must_change_password) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password), email, 1 if must_change else 0),
            )
            db.commit()
            return True
        except Exception:
            return False


def verify_admin(username, password):
    """Verify admin login credentials. Returns admin row or None."""
    with get_db() as db:
        admin = db.execute(
            "SELECT * FROM admin WHERE username = ?", (username,)
        ).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            return admin
        return None


def get_admin_by_id(admin_id):
    """Get admin by ID."""
    with get_db() as db:
        return db.execute("SELECT * FROM admin WHERE id = ?", (admin_id,)).fetchone()


def admin_exists():
    """Check if any admin account exists."""
    with get_db() as db:
        count = db.execute("SELECT COUNT(*) as cnt FROM admin").fetchone()["cnt"]
        return count > 0


def change_password(admin_id, old_password, new_password):
    """
    Change admin password. Returns (success, error_message).
    [FIX H3] Allows password change with old password verification.
    [FIX L5] Enforces password complexity.
    """
    # Validate new password strength
    if len(new_password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", new_password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[0-9]", new_password):
        return False, "Password must contain at least one digit."

    with get_db() as db:
        admin = db.execute("SELECT * FROM admin WHERE id = ?", (admin_id,)).fetchone()
        if not admin:
            return False, "Admin not found."

        if not check_password_hash(admin["password_hash"], old_password):
            return False, "Current password is incorrect."

        db.execute(
            "UPDATE admin SET password_hash = ?, must_change_password = 0 WHERE id = ?",
            (generate_password_hash(new_password), admin_id),
        )
        db.commit()
        return True, "Password changed successfully!"
