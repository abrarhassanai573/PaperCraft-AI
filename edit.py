import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
import streamlit as st


def _download(data, filename):
    st.download_button("Download PDF", data=data, file_name=filename, mime="application/pdf")


def rotate_pdf_ui():
    f=st.file_uploader("Upload PDF", type="pdf", key="rotate_file")
    if not f:return
    angle=st.selectbox("Rotation",[90,180,270], key="rotate_angle")
    if st.button("Rotate PDF", key="rotate_btn"):
        try:
            reader=PdfReader(f); writer=PdfWriter()
            for p in reader.pages: p.rotate(angle); writer.add_page(p)
            out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"rotated.pdf")
        except Exception as e: st.error(str(e))


def _overlay_page(width,height,text,opacity=0.18):
    b=io.BytesIO(); c=canvas.Canvas(b,pagesize=(width,height)); c.saveState(); c.setFillColor(Color(0.2,0.3,0.8,alpha=opacity)); c.setFont("Helvetica-Bold",36); c.translate(width/2,height/2); c.rotate(45); c.drawCentredString(0,0,text); c.restoreState(); c.save(); b.seek(0); return PdfReader(b).pages[0]


def watermark_ui():
    f=st.file_uploader("Upload PDF", type="pdf", key="watermark_file")
    text=st.text_input("Watermark text", "PaperCraft AI", key="watermark_text")
    if not f:return
    if st.button("Add Watermark", key="watermark_btn"):
        try:
            reader=PdfReader(f); writer=PdfWriter()
            for p in reader.pages:
                box=p.mediabox; overlay=_overlay_page(float(box.width),float(box.height),text); p.merge_page(overlay); writer.add_page(p)
            out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"watermarked.pdf")
        except Exception as e: st.error(str(e))


def page_numbers_ui():
    f=st.file_uploader("Upload PDF", type="pdf", key="numbers_file")
    position=st.selectbox("Position",["Bottom center","Bottom right","Bottom left"], key="number_position")
    if not f:return
    if st.button("Add Page Numbers", key="numbers_btn"):
        try:
            reader=PdfReader(f); writer=PdfWriter()
            for n,p in enumerate(reader.pages,1):
                box=p.mediabox; w,h=float(box.width),float(box.height)
                b=io.BytesIO(); c=canvas.Canvas(b,pagesize=(w,h)); c.setFont("Helvetica",9)
                x=w/2 if position=="Bottom center" else (w-30 if position=="Bottom right" else 30)
                c.drawCentredString(x,18,str(n)) if position=="Bottom center" else c.drawString(x,18,str(n)); c.save(); b.seek(0)
                p.merge_page(PdfReader(b).pages[0]); writer.add_page(p)
            out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"numbered.pdf")
        except Exception as e: st.error(str(e))
