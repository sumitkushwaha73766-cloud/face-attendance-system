"""Email notification service."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from config import Config


def send_email(to_email, subject, body_html):
    """Send an HTML email notification."""
    if not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
        print("Email not configured. Skipping notification.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = Config.SMTP_FROM_EMAIL or Config.SMTP_USERNAME
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_attendance_summary(to_email, summary, class_name="All Classes"):
    """Send daily attendance summary email."""
    subject = f"Attendance Summary - {date.today().strftime('%d %B %Y')}"

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #1F4E79;">📋 Daily Attendance Summary</h2>
        <p><strong>Date:</strong> {date.today().strftime('%d %B %Y')}</p>
        <p><strong>Class:</strong> {class_name}</p>
        <table style="border-collapse: collapse; width: 50%;">
            <tr style="background: #4472C4; color: white;">
                <th style="padding: 10px; border: 1px solid #ddd;">Metric</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Count</th>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Total Students</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{summary['total']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Present</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: green;">{summary['present']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Absent</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: red;">{summary['absent']}</td>
            </tr>
            <tr style="background: #f0f0f0;">
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Attendance %</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;"><strong>{summary['percentage']}%</strong></td>
            </tr>
        </table>
        <br>
        <p style="color: #888; font-size: 12px;">— Face Recognition Attendance System</p>
    </body>
    </html>
    """
    return send_email(to_email, subject, body)
