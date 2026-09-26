import io, os, tempfile
from pypdf import PdfReader, PdfWriter
import streamlit as st


def _download(data, filename):
    st.download_button("Download PDF", data=data, file_name=filename, mime="application/pdf")


def compress_pdf_ui():
    f=st.file_uploader("Upload a PDF", type="pdf", key="compress_file")
    if not f:return
    if st.button("Compress PDF", key="compress_btn"):
        try:
            import pikepdf
            with pikepdf.open(f) as pdf:
                out=io.BytesIO(); pdf.save(out, linearize=True, compress_streams=True)
                _download(out.getvalue(),"compressed.pdf")
        except ImportError:
            try:
                reader=PdfReader(f); writer=PdfWriter()
                for p in reader.pages: writer.add_page(p)
                out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"compressed.pdf")
                st.warning("pikepdf is not available; basic PDF rewrite was used.")
            except Exception as e: st.error(str(e))
        except Exception as e: st.error(f"Compression failed: {e}")


def repair_pdf_ui():
    f=st.file_uploader("Upload a PDF", type="pdf", key="repair_file")
    if not f:return
    if st.button("Repair PDF", key="repair_btn"):
        try:
            reader=PdfReader(f, strict=False); writer=PdfWriter()
            for p in reader.pages: writer.add_page(p)
            out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"repaired.pdf")
        except Exception as e: st.error(f"Repair failed: {e}")


def ocr_pdf_ui():
    f=st.file_uploader("Upload a scanned/image PDF", type="pdf", key="ocr_file")
    lang=st.text_input("Tesseract language", value="eng", key="ocr_lang")
    dpi=st.slider("Image DPI", 120, 300, 180, 10, key="ocr_dpi")
    if not f:return
    if st.button("Make Searchable PDF", key="ocr_btn"):
        try:
            from pdf2image import convert_from_bytes
            import pytesseract
            from PIL import Image
            pages=convert_from_bytes(f.getvalue(), dpi=dpi)
            writer=PdfWriter()
            progress=st.progress(0)
            for i,img in enumerate(pages):
                data=pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=lang)
                r=PdfReader(io.BytesIO(data)); writer.add_page(r.pages[0]); progress.progress((i+1)/len(pages))
            out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"searchable.pdf")
        except Exception as e: st.error(f"OCR failed. Make sure Tesseract and Poppler are installed. Details: {e}")
