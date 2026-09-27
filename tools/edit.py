import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io


def rotate_pdf_ui():
    st.write("Rotate PDF pages.")
    file = st.file_uploader("Upload PDF", type="pdf", key="rotate")
    angle = st.selectbox("Rotation angle", [90, 180, 270])
    if file and st.button("Rotate"):
        reader = PdfReader(file)
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(angle)
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        st.success(f"Rotated {angle}°!")
        st.download_button("Download rotated.pdf", buf.getvalue(), "rotated.pdf", "application/pdf")


def watermark_ui():
    st.write("Add a text watermark to your PDF.")
    file = st.file_uploader("Upload PDF", type="pdf", key="wm")
    text = st.text_input("Watermark text", value="CONFIDENTIAL")
    opacity = st.slider("Opacity", 0.1, 1.0, 0.3)
    if file and st.button("Add Watermark"):
        reader = PdfReader(file)
        page_w = float(reader.pages[0].mediabox.width)
        page_h = float(reader.pages[0].mediabox.height)

        wm_buf = io.BytesIO()
        c = canvas.Canvas(wm_buf, pagesize=(page_w, page_h))
        c.saveState()
        c.setFillAlpha(opacity)
        c.setFont("Helvetica-Bold", 50)
        c.translate(page_w / 2, page_h / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, text)
        c.restoreState()
        c.save()
        wm_buf.seek(0)
        watermark_page = PdfReader(wm_buf).pages[0]

        writer = PdfWriter()
        for page in reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        st.success("Watermark added!")
        st.download_button("Download watermarked.pdf", buf.getvalue(), "watermarked.pdf", "application/pdf")


def page_numbers_ui():
    st.write("Add page numbers to your PDF.")
    file = st.file_uploader("Upload PDF", type="pdf", key="pn")
    position = st.selectbox("Position", ["Bottom Center", "Bottom Right", "Bottom Left"])
    if file and st.button("Add Page Numbers"):
        reader = PdfReader(file)
        total = len(reader.pages)
        page_w = float(reader.pages[0].mediabox.width)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            num_buf = io.BytesIO()
            c = canvas.Canvas(num_buf, pagesize=(page_w, float(page.mediabox.height)))
            label = f"{i + 1} / {total}"
            if position == "Bottom Center":
                c.drawCentredString(page_w / 2, 20, label)
            elif position == "Bottom Right":
                c.drawRightString(page_w - 30, 20, label)
            else:
                c.drawString(30, 20, label)
            c.save()
            num_buf.seek(0)
            num_page = PdfReader(num_buf).pages[0]
            page.merge_page(num_page)
            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        st.success("Page numbers added!")
        st.download_button("Download numbered.pdf", buf.getvalue(), "numbered.pdf", "application/pdf")
