from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color

def generate_pdf_report(user_id, profile_text):
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

    filename = f"psychevision_profile_{user_id}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)

    # синій корпоративний колір
    header_color = Color(0/255, 51/255, 102/255)

    # Титул
    c.setFont("DejaVu", 26)
    c.setFillColor(header_color)
    c.drawString(50, 800, "PsycheVision · Психологічний профіль")

    # Основний текст
    c.setFont("DejaVu", 12)
    c.setFillColorRGB(0, 0, 0)

    y = 760
    for line in profile_text.split("\n"):
        c.drawString(50, y, line)
        y -= 18
        if y < 50:
            c.showPage()
            c.setFont("DejaVu", 12)
            y = 800

    c.save()
    return filename