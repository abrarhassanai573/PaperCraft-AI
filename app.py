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


def _generate_ai(prompt):
    errors = []
    try:
        key = _secret("GEMINI_API_KEY")
        if not key: raise RuntimeError("GEMINI_API_KEY is not configured.")
        from google import genai
        client = genai.Client(api_key=key)
        model = _secret("GEMINI_MODEL", "gemini-2.5-flash")
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text, "Gemini"
    except Exception as e:
        errors.append(f"Gemini: {e}")
    try:
        key = _secret("GROQ_API_KEY")
        if not key: raise RuntimeError("GROQ_API_KEY is not configured.")
        from groq import Groq
        client = Groq(api_key=key)
        model = _secret("GROQ_MODEL", "llama-3.3-70b-versatile")
        response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], temperature=0.2)
        return response.choices[0].message.content, "Groq"
    except Exception as e:
        errors.append(f"Groq: {e}")
    raise RuntimeError("No AI provider succeeded. " + " | ".join(errors))


def _text_from_pdf(data, max_chars=50000):
    reader = PdfReader(io.BytesIO(data)); chunks = []; total = 0
    for i, p in enumerate(reader.pages):
        try: txt = p.extract_text() or ""
        except Exception: txt = ""
        if txt.strip():
            chunk = f"\n--- Page {i+1} ---\n{txt}"
            chunks.append(chunk); total += len(chunk)
        if total >= max_chars: break
    return "".join(chunks)[:max_chars]


def _ai_upload(key):
    return st.file_uploader("Upload PDF", type="pdf", key=key)


def summarizer_ui():
    f = _ai_upload("ai_summary_file")
    if not f: return
    if st.button("Summarize with AI", key="summary_btn"):
        text = _text_from_pdf(f.getvalue())
        if not text.strip(): st.warning("No selectable text found in this PDF."); return
        try:
            result, provider = _generate_ai("Summarize this PDF clearly. Give a short overview, key points, important facts, and action items if present.\n\n" + text)
            st.caption(f"Generated with {provider}"); st.markdown(result)
        except Exception as e: st.error(str(e))


def pdf_to_markdown_ui():
    f = _ai_upload("ai_md_file")
    if not f: return
    if st.button("Convert to Markdown", key="md_btn"):
        text = _text_from_pdf(f.getvalue())
        if not text.strip(): st.warning("No selectable text found."); return
        try:
            result, provider = _generate_ai("Convert the following document into clean Markdown. Preserve headings, lists, tables where possible, and do not invent content.\n\n" + text)
            st.caption(f"Generated with {provider}"); st.code(result, language="markdown")
            st.download_button("Download Markdown", result, file_name="document.md", mime="text/markdown")
        except Exception as e: st.error(str(e))


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


# ---------- UI ----------
st.markdown("""
<style>
:root { --primary:#4F46E5; --primary-dark:#4338CA; --accent:#14B8A6; --bg:#F8FAFC; --card-bg:#FFFFFF; --text:#1E293B; --muted:#64748B; }
.stApp { background:var(--bg); }
#MainMenu, footer, header { visibility:hidden; }
.pc-navbar { display:flex; align-items:center; justify-content:space-between; padding:14px 6px; margin-bottom:8px; border-bottom:1px solid #E2E8F0; }
.pc-logo { font-size:1.5rem; font-weight:800; color:var(--text); }
.pc-logo span { color:var(--primary); }
.pc-tagline { color:var(--muted); font-size:.9rem; }
.pc-section-title { font-size:1.05rem; font-weight:700; color:var(--text); margin:22px 0 10px 2px; display:flex; align-items:center; gap:8px; }
.pc-badge { background:var(--accent); color:white; font-size:.65rem; padding:2px 8px; border-radius:999px; font-weight:700; text-transform:uppercase; letter-spacing:.03em; }
div[data-testid="stButton"] > button { width:100%; text-align:left; background:var(--card-bg); border:1px solid #E2E8F0; border-radius:12px; padding:16px 14px; font-weight:600; color:var(--text); box-shadow:0 1px 2px rgba(0,0,0,.03); transition:all .15s ease; }
div[data-testid="stButton"] > button:hover { border-color:var(--primary); box-shadow:0 4px 12px rgba(79,70,229,.15); color:var(--primary); transform:translateY(-1px); }
.pc-back button { width:auto !important; background:transparent !important; border:none !important; color:var(--primary) !important; font-weight:700 !important; padding:4px 0 !important; box-shadow:none !important; }
.pc-back button:hover { text-decoration:underline; transform:none; }
h1 { color:var(--text) !important; }
.stDownloadButton button { background:var(--primary) !important; color:white !important; border:none !important; border-radius:8px !important; font-weight:600 !important; }
.stDownloadButton button:hover { background:var(--primary-dark) !important; }
</style>
""", unsafe_allow_html=True)

TOOLS = {
    "Organize PDF": {"icon":"🗂️", "items": {"Merge PDF":("📑",merge_pdf_ui), "Split PDF":("✂️",split_pdf_ui), "Remove Pages":("🗑️",remove_pages_ui), "Extract Pages":("📤",extract_pages_ui), "Reorder Pages":("🔀",reorder_pages_ui)}},
    "Optimize PDF": {"icon":"⚡", "items": {"Compress PDF":("📉",compress_pdf_ui), "Repair PDF":("🛠️",repair_pdf_ui), "OCR PDF":("🔍",ocr_pdf_ui)}},
    "Convert PDF": {"icon":"🔄", "items": {"PDF to JPG":("🖼️",pdf_to_jpg_ui), "JPG to PDF":("📷",jpg_to_pdf_ui), "PDF to Word":("📝",pdf_to_word_ui), "Word to PDF":("📄",word_to_pdf_ui), "Excel to PDF":("📊",excel_to_pdf_ui), "PowerPoint to PDF":("📽️",ppt_to_pdf_ui), "PDF to Excel":("📈",pdf_to_excel_ui)}},
    "Edit PDF": {"icon":"✏️", "items": {"Rotate PDF":("🔁",rotate_pdf_ui), "Add Watermark":("💧",watermark_ui), "Page Numbers":("🔢",page_numbers_ui)}},
    "PDF Security": {"icon":"🔒", "items": {"Protect PDF":("🔐",protect_pdf_ui), "Unlock PDF":("🔓",unlock_pdf_ui)}},
    "AI Intelligence": {"icon":"🧠", "badge":"Unique", "items": {"AI Summarizer":("🧠",summarizer_ui), "PDF to Markdown":("📋",pdf_to_markdown_ui), "Ask Your PDF":("💬",chat_with_pdf_ui), "Smart Data Extractor":("🎯",smart_extractor_ui)}},
}

if "tool" not in st.session_state:
    st.session_state.tool = None

st.markdown('''<div class="pc-navbar"><div><div class="pc-logo">Paper<span>Craft</span> AI</div><div class="pc-tagline">Free, professional PDF tools — with AI superpowers</div></div></div>''', unsafe_allow_html=True)

if st.session_state.tool is None:
    for category, data in TOOLS.items():
        badge = f'<span class="pc-badge">{data["badge"]}</span>' if "badge" in data else ""
        st.markdown(f'<div class="pc-section-title">{data["icon"]} {category} {badge}</div>', unsafe_allow_html=True)
        items = list(data["items"].items()); cols = st.columns(4)
        for i, (name, (icon, handler)) in enumerate(items):
            with cols[i % 4]:
                if st.button(f"{icon}  {name}", key=f"card_{category}_{name}"):
                    st.session_state.tool = (name, handler); st.rerun()
else:
    name, handler = st.session_state.tool
    st.markdown('<div class="pc-back">', unsafe_allow_html=True)
    if st.button("← Back to all tools"):
        st.session_state.tool = None; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.title(name)
    handler()

st.markdown("---")
st.caption("PaperCraft AI · 100% free · open source · GitHub")
