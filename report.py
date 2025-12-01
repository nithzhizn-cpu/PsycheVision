
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

def generate_pdf_report(user_id: int, profile_text: str, path: str | None = None) -> str:
    if path is None:
        path = f"psychevision_profile_{user_id}.pdf"

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # Заголовок
    c.setFillColor(colors.HexColor("#0F3D73"))
    c.setFont("Helvetica-Bold", 20)
    c.drawString(72, height - 72, "PsycheVision — Psychological Profile")

    # Тіло звіту
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    text_obj = c.beginText(72, height - 110)
    for line in profile_text.split("\n"):
        text_obj.textLine(line)
    c.drawText(text_obj)

    c.showPage()
    c.save()
    return path
