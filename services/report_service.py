"""
Report generation service — Excel and PDF exports.
[FIX M5] Uses tempfile to avoid unbounded disk growth.
"""
import os
import tempfile
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from fpdf import FPDF


def generate_excel_report(attendance_data, filename=None):
    """
    Generate an Excel attendance report to a temporary file.
    Returns: filepath of the generated Excel file.
    """
    if filename is None:
        filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    filepath = os.path.join(tempfile.gettempdir(), filename)

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance Report"

    # Styles
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Title
    ws.merge_cells("A1:G1")
    title_cell = ws["A1"]
    title_cell.value = "Face Recognition Attendance Report"
    title_cell.font = Font(bold=True, size=16, color="1F4E79")
    title_cell.alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:G2")
    ws["A2"].value = f"Generated on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}"
    ws["A2"].alignment = Alignment(horizontal="center")

    # Headers
    headers = ["#", "Date", "Time", "Name", "Roll No", "Class", "Status"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Data rows
    for idx, row in enumerate(attendance_data, 1):
        data = [
            idx,
            row["date"],
            row["time"],
            row["name"],
            row["roll_no"],
            f"{row['class_name']} - {row['section']}",
            row["status"],
        ]
        for col, value in enumerate(data, 1):
            cell = ws.cell(row=idx + 4, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center")

    # Auto-fit column widths
    for col in ws.columns:
        max_length = 0
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col[0].column_letter].width = max_length + 4

    # Summary row
    summary_row = len(attendance_data) + 6
    ws.cell(row=summary_row, column=1, value="Total Records:").font = Font(bold=True)
    ws.cell(row=summary_row, column=2, value=len(attendance_data))

    wb.save(filepath)
    return filepath


def generate_pdf_report(attendance_data, filename=None):
    """
    Generate a PDF attendance report to a temporary file.
    Returns: filepath of the generated PDF file.
    """
    if filename is None:
        filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    filepath = os.path.join(tempfile.gettempdir(), filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "Face Recognition Attendance Report", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(68, 114, 196)
    pdf.set_text_color(255, 255, 255)

    col_widths = [10, 25, 20, 45, 25, 35, 20]
    headers = ["#", "Date", "Time", "Name", "Roll No", "Class", "Status"]

    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=1, align="C", fill=True)
    pdf.ln()

    # Table data
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)

    for idx, row in enumerate(attendance_data, 1):
        data = [
            str(idx),
            row["date"],
            row["time"],
            row["name"],
            row["roll_no"],
            f"{row['class_name']}-{row['section']}",
            row["status"],
        ]
        for w, d in zip(col_widths, data):
            pdf.cell(w, 7, d, border=1, align="C")
        pdf.ln()

    # Summary
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Total Records: {len(attendance_data)}", new_x="LMARGIN", new_y="NEXT")

    pdf.output(filepath)
    return filepath
