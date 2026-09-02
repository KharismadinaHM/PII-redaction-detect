"""
generate_dummy_pdf.py
Generates a hybrid test PDF containing:
  - Page 1: Native text with employee PII data (text embedded in PDF)
  - Page 2: Image-based scan simulation (text rendered to image, embedded in PDF)

Outputs to data/dummy_hybrid.pdf
"""

import fitz  # PyMuPDF
import os
from PIL import Image, ImageDraw, ImageFont
import io


# ── Sample PII data for the dummy PDF ──
EMPLOYEE_DATA = {
    "Nama": "Budi Santoso",
    "NIK": "3201150708900001",
    "No. HP": "081234567890",
    "Email": "budi.santoso@perusahaan.co.id",
    "Alamat": "Jl. Merdeka No. 1, Jakarta Pusat 10110",
    "Gaji": "Rp 15.000.000",
    "NPWP": "12.345.678.9-012.345",
}

EMPLOYEE_DATA_2 = {
    "Nama": "Siti Rahayu",
    "NIK": "3202230411850002",
    "No. HP": "+6285298765432",
    "Email": "siti.rahayu@kantor.com",
    "Alamat": "Gg. Kenanga No. 5, Bandung 40115",
    "Gaji": "Rp 8.500.000",
    "NPWP": "98.765.432.1-098.765",
}


def _render_text_to_image(data: dict, title: str = "Employee Record (Scanned)") -> Image.Image:
    """
    Renders employee data as a simulated scanned document image.
    Creates an A4-proportioned white image with black text.

    Returns:
        PIL Image object.
    """
    width, height = 1240, 1754  # A4 at 150dpi approx
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Try to load a system monospace font; fallback to default
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        font_body = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except Exception:
        font_title = ImageFont.load_default()
        font_body = font_title
        font_small = font_title

    # Header / title
    draw.text((80, 80), title, fill=(20, 20, 20), font=font_title)
    draw.line([(80, 135), (width - 80, 135)], fill=(80, 80, 80), width=3)

    # Document label
    draw.text(
        (80, 155),
        "CONFIDENTIAL — Internal HR Document",
        fill=(160, 40, 40),
        font=font_small,
    )

    # Employee fields
    y = 220
    line_height = 65
    for label, value in data.items():
        draw.text((80, y), f"{label}:", fill=(60, 60, 60), font=font_small)
        draw.text((280, y), str(value), fill=(10, 10, 10), font=font_body)
        y += line_height

    # Footer
    draw.line([(80, height - 160), (width - 80, height - 160)], fill=(180, 180, 180), width=2)
    draw.text(
        (80, height - 140),
        "Document scanned via HR Digitization System — For internal use only.",
        fill=(130, 130, 130),
        font=font_small,
    )
    draw.text(
        (80, height - 100),
        "Unauthorized distribution is prohibited.",
        fill=(130, 130, 130),
        font=font_small,
    )

    return img


def _add_native_text_page(doc: fitz.Document, data: dict, title: str, add_embedded_image: bool = False) -> None:
    """
    Adds a native-text page to the PDF document using PyMuPDF text insertion.

    Args:
        doc: The PyMuPDF Document to add the page to.
        data: Employee data dict.
        title: Page title string.
        add_embedded_image: If True, adds a small simulated scan image to the page.
    """
    page = doc.new_page(width=595, height=842)  # A4 in points

    # Title
    page.insert_text(
        fitz.Point(50, 60),
        title,
        fontsize=18,
        fontname="helv",
        color=(0.05, 0.05, 0.4),
    )

    # Horizontal rule (drawn as a thin rectangle)
    page.draw_rect(fitz.Rect(50, 70, 545, 72), color=(0.5, 0.5, 0.5), fill=(0.5, 0.5, 0.5))

    # Subtitle
    page.insert_text(
        fitz.Point(50, 88),
        "CONFIDENTIAL — Internal HR Record (Native Text)",
        fontsize=10,
        fontname="helv",
        color=(0.6, 0.1, 0.1),
    )

    # Employee fields
    y = 115
    line_height = 22
    for label, value in data.items():
        page.insert_text(
            fitz.Point(50, y),
            f"{label}:",
            fontsize=11,
            fontname="helv",
            color=(0.3, 0.3, 0.3),
        )
        page.insert_text(
            fitz.Point(150, y),
            str(value),
            fontsize=11,
            fontname="helv",
            color=(0.05, 0.05, 0.05),
        )
        y += line_height

    # Embedded image (simulating a scanned attachment within a text page)
    if add_embedded_image:
        page.insert_text(
            fitz.Point(50, y + 20),
            "Attached Scanned ID:",
            fontsize=11,
            fontname="helv",
            color=(0.3, 0.3, 0.3),
        )
        small_img = _render_text_to_image({"ID NIK": "1111222233334444"}, title="Scanned KTP Crop")
        # Resize to make it small enough to fit
        small_img.thumbnail((400, 300))
        buf = io.BytesIO()
        small_img.save(buf, format="PNG")
        
        # Insert image at bottom of the page
        img_y = y + 40
        page.insert_image(fitz.Rect(50, img_y, 50 + small_img.width * 0.4, img_y + small_img.height * 0.4), stream=buf.getvalue())


    # Footer note
    page.insert_text(
        fitz.Point(50, 800),
        "This page contains native text — PII will be detected by regex + NER engine.",
        fontsize=9,
        fontname="helv",
        color=(0.5, 0.5, 0.5),
    )


def _add_image_page(doc: fitz.Document, img: Image.Image) -> None:
    """
    Adds an image-based (scan-simulated) page by embedding a PIL Image into the PDF.

    Args:
        doc: PyMuPDF Document.
        img: PIL Image representing the scanned page.
    """
    page = doc.new_page(width=595, height=842)  # A4

    # Convert PIL image to bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    # Insert image to fill the entire page
    page.insert_image(fitz.Rect(0, 0, 595, 842), stream=img_bytes)


def generate_dummy_pdf(output_path: str = None) -> str:
    """
    Generates a 3-page hybrid test PDF:
      - Page 1: Native text (Employee 1 data)
      - Page 2: Native text (Employee 2 data)
      - Page 3: Image-based scan (Employee 1 data rendered as image)

    Args:
        output_path: Destination file path. Defaults to data/dummy_hybrid.pdf.

    Returns:
        Path to the generated PDF file.
    """
    if output_path is None:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        output_path = os.path.join(data_dir, "dummy_hybrid.pdf")

    doc = fitz.open()  # New empty PDF

    # Page 1: Native text — Employee 1
    _add_native_text_page(
        doc,
        EMPLOYEE_DATA,
        "Employee Personal Record — Budi Santoso",
        add_embedded_image=True,
    )

    # Page 2: Native text — Employee 2
    _add_native_text_page(
        doc,
        EMPLOYEE_DATA_2,
        "Employee Personal Record — Siti Rahayu",
    )

    # Page 3: Image-based — Employee 1 scan simulation
    scanned_img = _render_text_to_image(
        EMPLOYEE_DATA,
        title="Employee Record (Scanned KTP Attachment)",
    )
    _add_image_page(doc, scanned_img)

    doc.save(output_path)
    doc.close()
    print(f"Generated hybrid PDF: {output_path}")
    print(f"  Pages 1-2: Native text (extractable)")
    print(f"  Page 3: Image-based scan simulation (requires OCR)")
    return output_path


if __name__ == "__main__":
    generate_dummy_pdf()
