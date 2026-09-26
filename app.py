import io
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import streamlit as st
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="PaperCraft AI — Free PDF Tools", page_icon="🧾", layout="wide")

# ---------------------------------------------------------------------------
# PaperCraft AI — single-file deployment version
# This version intentionally keeps all tool handlers inside app.py so the app
# does not depend on a missing `tools/` package in Streamlit Cloud.
# ---------------------------------------------------------------------------

# ---------- Common helpers ----------
def _download_pdf(data, filename="output.pdf", label="Download PDF"):
    st.download_button(label, data=data, file_name=filename, mime="application/pdf")


def _parse_ranges(spec, total):
    result = []
    for part in spec.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = int(a), int(b)
            if start > end:
                start, end = end, start
            result.extend(range(start - 1, end))
        else:
            result.append(int(part) - 1)
    if not result or any(i < 0 or i >= total for i in result):
        raise ValueError("Invalid page range.")
    return result


# ---------- Organize PDF ----------
def merge_pdf_ui():
    files = st.file_uploader("Upload 2 or more PDF files", type="pdf", accept_multiple_files=True, key="merge_files")
    if st.button("Merge PDFs", key="merge_btn", disabled=len(files) < 2):
        try:
            writer = PdfWriter()
            for f in files:
                for page in PdfReader(f).pages:
                    writer.add_page(page)
            out = io.BytesIO(); writer.write(out)
            _download_pdf(out.getvalue(), "merged.pdf")
        except Exception as e:
            st.error(f"Could not merge PDFs: {e}")


def split_pdf_ui():
    f = st.file_uploader("Upload a PDF", type="pdf", key="split_file")
    if not f: return
    reader = PdfReader(f)
    st.caption(f"Pages: {len(reader.pages)}")
    pages = st.text_input("Pages to extract (e.g. 1-3,5,8-10)", value=f"1-{len(reader.pages)}", key="split_pages")
    if st.button("Split / Extract", key="split_btn"):
        try:
            writer = PdfWriter()
            for i in _parse_ranges(pages, len(reader.pages)):
                writer.add_page(reader.pages[i])
            out = io.BytesIO(); writer.write(out)
            _download_pdf(out.getvalue(), "split.pdf")
        except Exception as e: st.error(str(e))


def remove_pages_ui():
    f = st.file_uploader("Upload a PDF", type="pdf", key="remove_file")
    if not f: return
    reader = PdfReader(f); st.caption(f"Pages: {len(reader.pages)}")
    spec = st.text_input("Pages to remove (e.g. 2,4-6)", key="remove_pages")
    if st.button("Remove Pages", key="remove_btn"):
        try:
            remove = set(_parse_ranges(spec, len(reader.pages)))
            writer = PdfWriter()
            for i, page in enumerate(reader.pages):
                if i not in remove: writer.add_page(page)
            out = io.BytesIO(); writer.write(out)
            _download_pdf(out.getvalue(), "pages_removed.pdf")
        except Exception as e: st.error(str(e))


def extract_pages_ui():
    f = st.file_uploader("Upload a PDF", type="pdf", key="extract_file")
    if not f: return
    reader = PdfReader(f); st.caption(f"Pages: {len(reader.pages)}")
    spec = st.text_input("Pages to extract (e.g. 1,3-5)", key="extract_pages")
    if st.button("Extract Pages", key="extract_btn"):
        try:
            writer = PdfWriter()
            for i in _parse_ranges(spec, len(reader.pages)):
                writer.add_page(reader.pages[i])
            out = io.BytesIO(); writer.write(out)
            _download_pdf(out.getvalue(), "extracted_pages.pdf")
        except Exception as e: st.error(str(e))


def reorder_pages_ui():
    f = st.file_uploader("Upload a PDF", type="pdf", key="reorder_file")
    if not f: return
    reader = PdfReader(f); total = len(reader.pages)
    st.info(f"Enter the new order using page numbers 1–{total}. Example: 3,1,2")
    order = st.text_input("New page order", value=",".join(map(str, range(1, total + 1))), key="order_pages")
    if st.button("Reorder Pages", key="reorder_btn"):
        try:
            indices = [int(x.strip()) - 1 for x in order.split(",") if x.strip()]
            if sorted(indices) != list(range(total)): raise ValueError("Use every page exactly once.")
            writer = PdfWriter()
            for i in indices: writer.add_page(reader.pages[i])
            out = io.BytesIO(); writer.write(out)
            _download_pdf(out.getvalue(), "reordered.pdf")
        except Exception as e: st.error(str(e))


# ---------- Optimize PDF ----------
def compress_pdf_ui():
    f = st.file_uploader("Upload a PDF", type="pdf", key="compress_file")
    if not f: return
    if st.button("Compress PDF", key="compress_btn"):
        try:
            import pikepdf
            with pikepdf.open(f) as pdf:
                out = io.BytesIO(); pdf.save(out, linearize=True, compress_streams=True)
                _download_pdf(out.getvalue(), "compressed.pdf")
        except ImportError:
            try:
                reader = PdfReader(f); writer = PdfWriter()
                for p in reader.pages: writer.add_page(p)
                out = io.BytesIO(); writer.write(out)
                _download_pdf(out.getvalue(), "compressed.pdf")
                st.warning("pikepdf is not available; basic PDF rewrite was used.")
            except Exception as e: st.error(str(e))
        except Exception as e: st.error(f"Compression failed: {e}")


def repair_pdf_ui():
    f = st.file_uploader("Upload a PDF", type="pdf", key="repair_file")
    if not f: return
    if st.button("Repair PDF", key="repair_btn"):
        try:
            reader = PdfReader(f, strict=False); writer = PdfWriter()
            for p in reader.pages: writer.add_page(p)
            out = io.BytesIO(); writer.write(out)
            _download_pdf(out.getvalue(), "repaired.pdf")
        except Exception as e: st.error(f"Repair failed: {e}")


def ocr_pdf_ui():
    f = st.file_uploader("Upload a scanned/image PDF", type="pdf", key="ocr_file")
    lang = st.text_input("Tesseract language", value="eng", key="ocr_lang")
    dpi = st.slider("Image DPI", 120, 300, 180, 10, key="ocr_dpi")
    if not f: return
    if st.button("Make Searchable PDF", key="ocr_btn"):
        try:
            from pdf2image import convert_from_bytes
            import pytesseract
            pages = convert_from_bytes(f.getvalue(), dpi=dpi)
            writer = PdfWriter(); progress = st.progress(0)
            for i, img in enumerate(pages):
                data = pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=lang)
                r = PdfReader(io.BytesIO(data)); writer.add_page(r.pages[0])
                progress.progress((i + 1) / len(pages))
            out = io.BytesIO(); writer.write(out)
            _download_pdf(out.getvalue(), "searchable.pdf")
        except Exception as e:
            st.error(f"OCR failed. Make sure Tesseract and Poppler are installed. Details: {e}")


# ---------- Convert PDF ----------
def _download(data, filename, mime):
    st.download_button("Download", data=data, file_name=filename, mime=mime)


def pdf_to_jpg_ui():
    f = st.file_uploader("Upload PDF", type="pdf", key="pdf_jpg_file")
    if not f: return
    if st.button("Convert to JPG", key="pdf_jpg_btn"):
        try:
            from pdf2image import convert_from_bytes
            pages = convert_from_bytes(f.getvalue(), dpi=150)
            if len(pages) == 1:
                b = io.BytesIO(); pages[0].convert("RGB").save(b, "JPEG", quality=92)
                _download(b.getvalue(), "page-1.jpg", "image/jpeg")
            else:
                z = io.BytesIO()
                with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zz:
                    for i, p in enumerate(pages, 1):
                        b = io.BytesIO(); p.convert("RGB").save(b, "JPEG", quality=92)
                        zz.writestr(f"page-{i}.jpg", b.getvalue())
                _download(z.getvalue(), "pdf-pages.zip", "application/zip")
        except Exception as e: st.error(f"Conversion failed: {e}")


def jpg_to_pdf_ui():
    files = st.file_uploader("Upload JPG/PNG images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="jpg_pdf_files")
    if not files: return
    if st.button("Create PDF", key="jpg_pdf_btn"):
        try:
            from PIL import Image
            imgs = [Image.open(f).convert("RGB") for f in files]
            out = io.BytesIO(); imgs[0].save(out, format="PDF", save_all=True, append_images=imgs[1:])
            _download(out.getvalue(), "images.pdf", "application/pdf")
        except Exception as e: st.error(str(e))


def _run_libreoffice(src_bytes, input_name, output_ext):
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / input_name; src.write_bytes(src_bytes)
        outdir = Path(td) / "out"; outdir.mkdir()
        subprocess.run(["soffice", "--headless", "--convert-to", output_ext, "--outdir", str(outdir), str(src)], check=True, capture_output=True, text=True, timeout=120)
        result = outdir / (src.stem + "." + output_ext.split(":")[0])
        if not result.exists():
            matches = list(outdir.iterdir())
            if not matches: raise RuntimeError("LibreOffice produced no output.")
            result = matches[0]
        return result.read_bytes()


def pdf_to_word_ui():
    f = st.file_uploader("Upload PDF", type="pdf", key="pdf_word_file")
    if not f: return
    if st.button("Convert to Word", key="pdf_word_btn"):
        try:
            from pdf2docx import Converter
            with tempfile.TemporaryDirectory() as td:
                src = Path(td) / "input.pdf"; dst = Path(td) / "output.docx"; src.write_bytes(f.getvalue())
                cv = Converter(str(src)); cv.convert(str(dst)); cv.close()
                _download(dst.read_bytes(), "converted.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as e: st.error(f"PDF to Word failed: {e}")


def word_to_pdf_ui():
    f = st.file_uploader("Upload Word document", type=["doc", "docx"], key="word_pdf_file")
    if not f: return
    if st.button("Convert to PDF", key="word_pdf_btn"):
        try: _download(_run_libreoffice(f.getvalue(), f.name, "pdf"), "converted.pdf", "application/pdf")
        except Exception as e: st.error(f"Word to PDF failed. LibreOffice is required: {e}")


def excel_to_pdf_ui():
    f = st.file_uploader("Upload Excel workbook", type=["xls", "xlsx"], key="excel_pdf_file")
    if not f: return
    if st.button("Convert to PDF", key="excel_pdf_btn"):
        try: _download(_run_libreoffice(f.getvalue(), f.name, "pdf"), "converted.pdf", "application/pdf")
        except Exception as e: st.error(f"Excel to PDF failed. LibreOffice is required: {e}")


def ppt_to_pdf_ui():
    f = st.file_uploader("Upload PowerPoint", type=["ppt", "pptx"], key="ppt_pdf_file")
    if not f: return
    if st.button("Convert to PDF", key="ppt_pdf_btn"):
        try: _download(_run_libreoffice(f.getvalue(), f.name, "pdf"), "converted.pdf", "application/pdf")
        except Exception as e: st.error(f"PowerPoint to PDF failed. LibreOffice is required: {e}")


def pdf_to_excel_ui():
    f = st.file_uploader("Upload PDF containing tables", type="pdf", key="pdf_excel_file")
    if not f: return
    if st.button("Extract Tables to Excel", key="pdf_excel_btn"):
        try:
            import pdfplumber
            from openpyxl import Workbook
            wb = Workbook(); ws = wb.active; ws.title = "Extracted Tables"
            row = 1; found = 0
            with pdfplumber.open(io.BytesIO(f.getvalue())) as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables() or []:
                        found += 1
                        for r in table:
                            for c, val in enumerate(r, 1): ws.cell(row=row, column=c, value=val)
                            row += 1
                        row += 1
            if not found: st.warning("No tables were detected."); return
            out = io.BytesIO(); wb.save(out)
            _download(out.getvalue(), "extracted_tables.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e: st.error(f"PDF to Excel failed: {e}")


# ---------- Edit PDF ----------
def rotate_pdf_ui():
    f = st.file_uploader("Upload PDF", type="pdf", key="rotate_file")
    if not f: return
    angle = st.selectbox("Rotation", [90, 180, 270], key="rotate_angle")
    if st.button("Rotate PDF", key="rotate_btn"):
        try:
            reader = PdfReader(f); writer = PdfWriter()
            for p in reader.pages: p.rotate(angle); writer.add_page(p)
            out = io.BytesIO(); writer.write(out); _download_pdf(out.getvalue(), "rotated.pdf")
        except Exception as e: st.error(str(e))


def _overlay_page(width, height, text, opacity=0.18):
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import Color
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=(width, height)); c.saveState()
    c.setFillColor(Color(0.2, 0.3, 0.8, alpha=opacity)); c.setFont("Helvetica-Bold", 36)
    c.translate(width / 2, height / 2); c.rotate(45); c.drawCentredString(0, 0, text); c.restoreState(); c.save(); b.seek(0)
    return PdfReader(b).pages[0]


def watermark_ui():
    f = st.file_uploader("Upload PDF", type="pdf", key="watermark_file")
    text = st.text_input("Watermark text", "PaperCraft AI", key="watermark_text")
    if not f: return
    if st.button("Add Watermark", key="watermark_btn"):
        try:
            reader = PdfReader(f); writer = PdfWriter()
            for p in reader.pages:
                box = p.mediabox; overlay = _overlay_page(float(box.width), float(box.height), text)
                p.merge_page(overlay); writer.add_page(p)
            out = io.BytesIO(); writer.write(out); _download_pdf(out.getvalue(), "watermarked.pdf")
        except Exception as e: st.error(str(e))


def page_numbers_ui():
    f = st.file_uploader("Upload PDF", type="pdf", key="numbers_file")
    position = st.selectbox("Position", ["Bottom center", "Bottom right", "Bottom left"], key="number_position")
    if not f: return
    if st.button("Add Page Numbers", key="numbers_btn"):
        try:
            from reportlab.pdfgen import canvas
            reader = PdfReader(f); writer = PdfWriter()
            for n, p in enumerate(reader.pages, 1):
                box = p.mediabox; w, h = float(box.width), float(box.height)
                b = io.BytesIO(); c = canvas.Canvas(b, pagesize=(w, h)); c.setFont("Helvetica", 9)
                x = w / 2 if position == "Bottom center" else (w - 30 if position == "Bottom right" else 30)
                if position == "Bottom center": c.drawCentredString(x, 18, str(n))
                else: c.drawString(x, 18, str(n))
                c.save(); b.seek(0); p.merge_page(PdfReader(b).pages[0]); writer.add_page(p)
            out = io.BytesIO(); writer.write(out); _download_pdf(out.getvalue(), "numbered.pdf")
        except Exception as e: st.error(str(e))


# ---------- PDF Security ----------
def protect_pdf_ui():
    f = st.file_uploader("Upload PDF", type="pdf", key="protect_file")
    pw = st.text_input("Password", type="password", key="protect_pw")
    if not f: return
    if st.button("Protect PDF", key="protect_btn"):
        if not pw: st.warning("Enter a password."); return
        try:
            reader = PdfReader(f); writer = PdfWriter()
            for p in reader.pages: writer.add_page(p)
            writer.encrypt(pw); out = io.BytesIO(); writer.write(out); _download_pdf(out.getvalue(), "protected.pdf")
        except Exception as e: st.error(str(e))


def unlock_pdf_ui():
    f = st.file_uploader("Upload protected PDF", type="pdf", key="unlock_file")
    pw = st.text_input("Current password", type="password", key="unlock_pw")
    if not f: return
    if st.button("Unlock PDF", key="unlock_btn"):
        try:
            reader = PdfReader(f)
            if reader.is_encrypted and reader.decrypt(pw) == 0: raise ValueError("Incorrect password.")
            writer = PdfWriter()
            for p in reader.pages: writer.add_page(p)
            out = io.BytesIO(); writer.write(out); _download_pdf(out.getvalue(), "unlocked.pdf")
        except Exception as e: st.error(f"Unlock failed: {e}")


# ---------- AI ----------
def _secret(name, default=None):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)

def ai_generate(prompt):
    """
    PaperCraft AI - Gemini + Groq fallback
    Uses current model names from Streamlit Secrets when provided.
    """

    gemini_key = get_secret("GEMINI_API_KEY") or get_secret("GOOGLE_API_KEY")
    groq_key = get_secret("GROQ_API_KEY")

    errors = []

    # =========================================================
    # GEMINI
    # =========================================================
    if gemini_key:
        try:
            from google import genai

            client = genai.Client(api_key=gemini_key)

            # Use the model configured in Streamlit Secrets.
            # Default is the model mentioned by your current API error.
            model = get_secret("GEMINI_MODEL") or "gemini-3.8-flash"

            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            result = getattr(response, "text", None)

            if result:
                return result.strip(), "Gemini"

            errors.append("Gemini returned an empty response.")

        except Exception as e:
            errors.append(
                f"Gemini: {type(e).__name__}: {str(e)[:500]}"
            )

    # =========================================================
    # GROQ
    # =========================================================
    if groq_key:
        try:
            from groq import Groq

            client = Groq(api_key=groq_key)

            # Put your currently available Groq model
            # in Streamlit Secrets as GROQ_MODEL.
            model = get_secret("GROQ_MODEL")

            if not model:
                raise RuntimeError(
                    "GROQ_MODEL is not configured in Streamlit Secrets."
                )

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are PaperCraft AI, a helpful document "
                            "assistant. Give accurate, concise answers."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )

            result = response.choices[0].message.content

            if result:
                return result.strip(), "Groq"

            errors.append("Groq returned an empty response.")

        except Exception as e:
            errors.append(
                f"Groq: {type(e).__name__}: {str(e)[:500]}"
            )

    # =========================================================
    # NO PROVIDER WORKED
    # =========================================================
    if not gemini_key and not groq_key:
        raise RuntimeError(
            "No AI API key is configured. "
            "Add GEMINI_API_KEY and/or GROQ_API_KEY "
            "in Streamlit Secrets."
        )

    raise RuntimeError(
        "No AI provider succeeded. " + " | ".join(errors)
    )


def chat_with_pdf_ui():
    f = _ai_upload("ai_chat_file")
    if not f: return
    text = _text_from_pdf(f.getvalue())
    if "ai_chat_history" not in st.session_state: st.session_state.ai_chat_history = []
    for role, msg in st.session_state.ai_chat_history:
        with st.chat_message(role): st.markdown(msg)
    q = st.chat_input("Ask a question about your PDF")
    if q:
        st.session_state.ai_chat_history.append(("user", q)); st.chat_message("user").markdown(q)
        try:
            ans, provider = _generate_ai(f"Answer the user's question only from the document below. If the answer is not in the document, say that clearly.\n\nDOCUMENT:\n{text}\n\nQUESTION:\n{q}")
            st.session_state.ai_chat_history.append(("assistant", ans)); st.chat_message("assistant").markdown(ans); st.caption(f"Generated with {provider}")
        except Exception as e: st.error(str(e))


def smart_extractor_ui():
    f = _ai_upload("ai_extract_file")
    instruction = st.text_area("What should be extracted?", "Extract names, dates, amounts, invoice numbers, and other important fields.", key="extract_instruction")
    if not f: return
    if st.button("Extract Data", key="extract_btn"):
        text = _text_from_pdf(f.getvalue())
        if not text.strip(): st.warning("No selectable text found."); return
        try:
            result, provider = _generate_ai(f"Extract structured information from this document. Return valid JSON only. Do not invent values. Task: {instruction}\n\nDOCUMENT:\n{text}")
            cleaned = result.strip().removeprefix("```json").removesuffix("```").strip()
            try: st.json(json.loads(cleaned))
            except Exception: st.code(result, language="json")
            st.caption(f"Generated with {provider}")
        except Exception as e: st.error(str(e))



# ---------- Extra PDF utilities ----------
def scan_to_pdf_ui():
    files = st.file_uploader("Upload scanned images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="scan_files")
    if not files:
        return
    if st.button("Create PDF", key="scan_btn"):
        try:
            from PIL import Image
            images = [Image.open(f).convert("RGB") for f in files]
            out = io.BytesIO()
            images[0].save(out, format="PDF", save_all=True, append_images=images[1:])
            _download_pdf(out.getvalue(), "scanned_document.pdf")
        except Exception as e:
            st.error(f"Scan to PDF failed: {e}")


def sign_pdf_ui():
    f = st.file_uploader("Upload PDF", type="pdf", key="sign_file")
    signature = st.text_input("Signature text", "Signed by PaperCraft AI", key="signature_text")
    if not f:
        return
    if st.button("Sign PDF", key="sign_btn"):
        try:
            from reportlab.pdfgen import canvas
            reader = PdfReader(f); writer = PdfWriter()
            for page in reader.pages:
                box = page.mediabox; w, h = float(box.width), float(box.height)
                b = io.BytesIO(); c = canvas.Canvas(b, pagesize=(w, h))
                c.setFont("Helvetica-Bold", 11); c.drawString(36, 30, signature); c.save(); b.seek(0)
                page.merge_page(PdfReader(b).pages[0]); writer.add_page(page)
            out = io.BytesIO(); writer.write(out)
            _download_pdf(out.getvalue(), "signed.pdf")
        except Exception as e:
            st.error(f"Signing failed: {e}")


def crop_pdf_ui():
    f = st.file_uploader("Upload PDF", type="pdf", key="crop_file")
    margin = st.slider("Crop margin (points)", 0, 100, 20, key="crop_margin")
    if not f:
        return
    if st.button("Crop PDF", key="crop_btn"):
        try:
            reader = PdfReader(f); writer = PdfWriter()
            for page in reader.pages:
                box = page.mediabox
                page.cropbox.lower_left = (float(box.left) + margin, float(box.bottom) + margin)
                page.cropbox.upper_right = (float(box.right) - margin, float(box.top) - margin)
                writer.add_page(page)
            out = io.BytesIO(); writer.write(out)
            _download_pdf(out.getvalue(), "cropped.pdf")
        except Exception as e:
            st.error(f"Crop failed: {e}")


def redact_pdf_ui():
    f = st.file_uploader("Upload PDF", type="pdf", key="redact_file")
    pages = st.text_input("Pages to redact", "1", key="redact_pages")
    if not f:
        return
    if st.button("Redact selected pages", key="redact_btn"):
        try:
            from reportlab.pdfgen import canvas
            reader = PdfReader(f); writer = PdfWriter(); selected = set(_parse_ranges(pages, len(reader.pages)))
            for idx, page in enumerate(reader.pages):
                if idx in selected:
                    box = page.mediabox; w, h = float(box.width), float(box.height)
                    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=(w, h)); c.setFillColorRGB(0,0,0); c.rect(0,0,w,h,fill=1,stroke=0); c.save(); b.seek(0)
                    page.merge_page(PdfReader(b).pages[0])
                writer.add_page(page)
            out = io.BytesIO(); writer.write(out)
            _download_pdf(out.getvalue(), "redacted.pdf")
            st.warning("This simple redaction masks the selected pages visually. For legal redaction, verify that hidden PDF objects/text are also removed.")
        except Exception as e:
            st.error(f"Redaction failed: {e}")


def compare_pdf_ui():
    a = st.file_uploader("Original PDF", type="pdf", key="compare_a")
    b = st.file_uploader("Second PDF", type="pdf", key="compare_b")
    if not (a and b):
        return
    if st.button("Compare PDFs", key="compare_btn"):
        try:
            ta = _text_from_pdf(a.getvalue(), 30000).strip()
            tb = _text_from_pdf(b.getvalue(), 30000).strip()
            import difflib
            diff = list(difflib.unified_diff(ta.splitlines(), tb.splitlines(), fromfile="Original", tofile="Second", lineterm=""))
            st.text_area("Comparison", "\n".join(diff) if diff else "No text differences detected.", height=420)
        except Exception as e:
            st.error(f"Comparison failed: {e}")


def translate_pdf_ui():
    f = _ai_upload("ai_translate_file")
    language = st.selectbox("Translate to", ["English", "Urdu", "Roman Urdu", "Arabic", "French", "Spanish"], key="translate_language")
    if not f:
        return
    if st.button("Translate with AI", key="translate_btn"):
        text = _text_from_pdf(f.getvalue())
        if not text.strip():
            st.warning("No selectable text found in this PDF.")
            return
        try:
            result, provider = _generate_ai(f"Translate the document below into {language}. Preserve meaning, headings and lists. Do not invent content.\n\n{text}")
            st.caption(f"Generated with {provider}"); st.markdown(result)
            st.download_button("Download translation", result, file_name="translated_document.txt", mime="text/plain")
        except Exception as e:
            st.error(str(e))


def history_add(tool_name, filename=""):
    if "history" not in st.session_state:
        st.session_state.history = []
    from datetime import datetime
    st.session_state.history.insert(0, {"tool": tool_name, "file": filename or "No file", "time": datetime.now().strftime("%d %b %Y, %I:%M %p")})
    st.session_state.history = st.session_state.history[:20]


# ---------- I Love PDF-inspired PaperCraft UI ----------
st.markdown("""
<style>
:root { --red:#e5322d; --red-dark:#c9211d; --ink:#242424; --muted:#777; --bg:#f7f7f7; --card:#fff; --line:#e9e9e9; }
.stApp { background:var(--bg); color:var(--ink); }
#MainMenu, footer, header { visibility:hidden; }
.block-container { max-width:1260px; padding-top:0.7rem; padding-bottom:3rem; }
.pc-nav { background:#fff; border-bottom:1px solid var(--line); padding:13px 0; margin-bottom:25px; }
.pc-brand { font-size:25px; font-weight:900; letter-spacing:-1.3px; color:#242424; }
.pc-brand .craft { color:var(--red); }
.pc-brand small { display:block; font-size:9px; letter-spacing:.8px; color:#999; font-weight:600; margin-top:-2px; }
.pc-navitem { font-size:12px; font-weight:800; color:#3b3b3b; text-transform:uppercase; letter-spacing:.2px; }
.pc-login { font-size:12px; font-weight:700; color:#444; }
.pc-sign { background:var(--red); color:#fff; padding:8px 13px; border-radius:5px; font-size:12px; font-weight:800; }
.hero { text-align:center; padding:12px 0 10px; }
.hero h1 { font-size:38px; line-height:1.15; letter-spacing:-1.2px; margin:0; color:#242424; font-weight:800; }
.hero p { max-width:780px; margin:10px auto 18px; color:#777; font-size:15px; line-height:1.55; }
.pills { display:flex; justify-content:center; gap:9px; flex-wrap:wrap; margin-bottom:18px; }
.pill { border:1px solid #ddd; background:#fff; color:#666; border-radius:18px; padding:7px 14px; font-size:12px; font-weight:700; }
.pill.active { background:#242424; color:#fff; border-color:#242424; }
.section { margin-top:20px; }
.section h3 { font-size:17px; margin:0 0 11px; color:#333; }
.tool-card { background:#fff; border:1px solid #e5e5e5; border-radius:10px; padding:18px 16px 14px; min-height:125px; box-shadow:0 1px 2px rgba(0,0,0,.025); }
.tool-icon { font-size:26px; margin-bottom:10px; }
.tool-title { font-size:15px; font-weight:800; color:#333; margin-bottom:5px; }
.tool-desc { font-size:11px; color:#888; line-height:1.45; min-height:32px; }
div[data-testid="stButton"] > button { border:1px solid #e2e2e2; background:#fff; color:#333; border-radius:7px; font-weight:750; min-height:38px; }
div[data-testid="stButton"] > button:hover { border-color:var(--red); color:var(--red); background:#fff; }
.stDownloadButton button { background:var(--red) !important; border-color:var(--red) !important; color:#fff !important; border-radius:6px !important; }
.stDownloadButton button:hover { background:var(--red-dark) !important; }
.pc-footer { text-align:center; color:#999; font-size:11px; padding:25px 0; border-top:1px solid #e7e7e7; margin-top:35px; }
.history-card { background:#fff; border:1px solid #e5e5e5; border-radius:8px; padding:12px 14px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

TOOLS = {
    "Organize PDF": {"icon":"🗂️", "items": {
        "Merge PDF":("📑","Combine multiple PDFs into one file.",merge_pdf_ui),
        "Split PDF":("✂️","Extract selected pages from a PDF.",split_pdf_ui),
        "Remove Pages":("✕","Remove unwanted pages.",remove_pages_ui),
        "Extract Pages":("↗","Create a new PDF from selected pages.",extract_pages_ui),
        "Reorder Pages":("↕","Change the order of PDF pages.",reorder_pages_ui),
        "Scan to PDF":("▣","Turn images into one PDF.",scan_to_pdf_ui)}},
    "Optimize PDF": {"icon":"⚡", "items": {
        "Compress PDF":("▣","Reduce PDF file size.",compress_pdf_ui),
        "Repair PDF":("🔧","Rewrite a damaged PDF when possible.",repair_pdf_ui),
        "OCR PDF":("⌕","Make scanned pages searchable.",ocr_pdf_ui)}},
    "Convert PDF": {"icon":"↔", "items": {
        "PDF to JPG":("▧","Convert PDF pages to images.",pdf_to_jpg_ui),
        "JPG to PDF":("▧","Create PDF from images.",jpg_to_pdf_ui),
        "PDF to Word":("W","Convert PDF to editable Word.",pdf_to_word_ui),
        "Word to PDF":("W","Convert Word documents to PDF.",word_to_pdf_ui),
        "Excel to PDF":("X","Convert Excel workbooks to PDF.",excel_to_pdf_ui),
        "PowerPoint to PDF":("P","Convert presentations to PDF.",ppt_to_pdf_ui),
        "PDF to Excel":("X","Extract PDF tables to Excel.",pdf_to_excel_ui)}},
    "Edit PDF": {"icon":"✎", "items": {
        "Rotate PDF":("↻","Rotate PDF pages.",rotate_pdf_ui),
        "Add Watermark":("◆","Add a watermark to pages.",watermark_ui),
        "Page Numbers":("#","Add page numbers.",page_numbers_ui),
        "Crop PDF":("□","Crop page margins.",crop_pdf_ui)}},
    "PDF Security": {"icon":"▣", "items": {
        "Protect PDF":("🔒","Encrypt a PDF with a password.",protect_pdf_ui),
        "Unlock PDF":("🔓","Remove a known PDF password.",unlock_pdf_ui),
        "Sign PDF":("✓","Add a simple text signature.",sign_pdf_ui),
        "Redact PDF":("■","Mask selected PDF pages.",redact_pdf_ui),
        "Compare PDF":("≠","Compare extracted text between PDFs.",compare_pdf_ui)}},
    "PDF Intelligence": {"icon":"✦", "badge":"AI", "items": {
        "AI Summarizer":("✦","Summarize a document with AI.",summarizer_ui),
        "Translate PDF":("文","Translate PDF text with AI.",translate_pdf_ui),
        "PDF to Markdown":("M","Convert a document to Markdown.",pdf_to_markdown_ui),
        "Ask Your PDF":("?","Chat with your uploaded PDF.",chat_with_pdf_ui),
        "Smart Data Extractor":("⌘","Extract structured fields with AI.",smart_extractor_ui)}}
}

if "tool" not in st.session_state: st.session_state.tool = None
if "history" not in st.session_state: st.session_state.history = []

# Header / navigation
nav1, nav2, nav3, nav4, nav5, nav6, nav7 = st.columns([1.65,1.0,1.0,1.15,1.25,0.65,0.7])
with nav1:
    st.markdown('<div class="pc-brand">Paper<span class="craft">Craft</span> AI<small>FREE PDF TOOLS + AI</small></div>', unsafe_allow_html=True)
for col, label, key in [(nav2,"MERGE PDF","Merge PDF"),(nav3,"SPLIT PDF","Split PDF"),(nav4,"COMPRESS PDF","Compress PDF"),(nav5,"CONVERT PDF","PDF to JPG")]:
    with col:
        if st.button(label, key="nav_"+key.replace(" ","_")):
            for cat in TOOLS.values():
                if key in cat["items"]:
                    st.session_state.tool=(key,cat["items"][key][2]); break
            st.rerun()
with nav6:
    if st.button("HISTORY", key="nav_history"): st.session_state.tool=("History",None); st.rerun()
with nav7:
    st.markdown('<div class="pc-login">Login<br><span class="pc-sign">Sign up</span></div>', unsafe_allow_html=True)

if st.session_state.tool is None:
    st.markdown('<div class="hero"><h1>Every PDF tool you need in one place</h1><p>PaperCraft AI gives you simple, fast PDF tools at your fingertips. Merge, split, compress, convert, edit, secure and use AI with your documents.</p></div>', unsafe_allow_html=True)
    pill_html='<div class="pills">'
    for cat in TOOLS:
        pill_html += f'<span class="pill">{TOOLS[cat]["icon"]} {cat}</span>'
    pill_html += '</div>'
    st.markdown(pill_html, unsafe_allow_html=True)

    for category, data in TOOLS.items():
        badge = f' <span style="background:#242424;color:#fff;border-radius:10px;padding:3px 8px;font-size:9px;">{data["badge"]}</span>' if "badge" in data else ""
        st.markdown(f'<div class="section"><h3>{data["icon"]} {category}{badge}</h3></div>', unsafe_allow_html=True)
        items=list(data["items"].items())
        cols=st.columns(5)
        for i,(name,(icon,desc,handler)) in enumerate(items):
            with cols[i%5]:
                st.markdown(f'<div class="tool-card"><div class="tool-icon">{icon}</div><div class="tool-title">{name}</div><div class="tool-desc">{desc}</div></div>',unsafe_allow_html=True)
                if st.button("Open tool", key="open_"+category+"_"+name):
                    st.session_state.tool=(name,handler); history_add(name); st.rerun()
else:
    name, handler = st.session_state.tool
    if st.button("← Back to all tools", key="back_tools"): st.session_state.tool=None; st.rerun()
    if name == "History":
        st.title("History")
        if not st.session_state.history:
            st.info("No tools have been used in this session yet.")
        else:
            if st.button("Clear history", key="clear_history"):
                st.session_state.history=[]; st.rerun()
            for item in st.session_state.history:
                st.markdown(f'<div class="history-card"><b>{item["tool"]}</b><br><span style="color:#888;font-size:12px;">{item["file"]} · {item["time"]}</span></div>',unsafe_allow_html=True)
    else:
        st.title(name)
        handler()

st.markdown('<div class="pc-footer">PaperCraft AI · Free PDF tools · AI document intelligence · Built with Streamlit</div>', unsafe_allow_html=True)
