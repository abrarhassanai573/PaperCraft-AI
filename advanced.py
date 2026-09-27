import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io
import os
import re
import zipfile


# ---------------------------------------------------------------------------
# Visual Page Manager — thumbnail-based remove / extract / reorder
# (replaces "type page ranges" with an actual visual picker)
# ---------------------------------------------------------------------------
def visual_page_manager_ui():
    st.write("PDF ke pages ko thumbnail images ki shakal mein dekho — koi typing nahi, "
             "bas uncheck karke hatao ya position number badal ke reorder karo.")
    file = st.file_uploader("PDF upload karo", type="pdf", key="vpm")
    if not file:
        return

    from pdf2image import convert_from_bytes
    file_bytes = file.getvalue()

    if "vpm_pages" not in st.session_state or st.session_state.get("vpm_name") != file.name:
        with st.spinner("Thumbnails bana rahe hain..."):
            st.session_state.vpm_pages = convert_from_bytes(file_bytes, dpi=55)
            st.session_state.vpm_name = file.name
        total = len(st.session_state.vpm_pages)
        for i in range(total):
            st.session_state[f"vpm_keep_{i}"] = True
            st.session_state[f"vpm_pos_{i}"] = i + 1

    pages = st.session_state.vpm_pages
    total = len(pages)
    st.caption(f"Total pages: {total}")

    cols = st.columns(5)
    for i in range(total):
        with cols[i % 5]:
            st.image(pages[i], use_container_width=True)
            st.checkbox(f"Keep page {i + 1}", key=f"vpm_keep_{i}")
            st.number_input("New position", min_value=1, max_value=total, key=f"vpm_pos_{i}",
                             label_visibility="collapsed")

    if st.button("Apply Changes"):
        requested = [(st.session_state[f"vpm_pos_{i}"], i) for i in range(total)
                     if st.session_state[f"vpm_keep_{i}"]]
        requested.sort(key=lambda x: x[0])
        new_order = [idx for _, idx in requested]

        reader = PdfReader(io.BytesIO(file_bytes))
        writer = PdfWriter()
        for idx in new_order:
            writer.add_page(reader.pages[idx])
        buf = io.BytesIO()
        writer.write(buf)
        st.success(f"Done! {len(new_order)} page(s) in the new PDF.")
        st.download_button("Download result.pdf", buf.getvalue(), "result.pdf", "application/pdf")


# ---------------------------------------------------------------------------
# Auto-Redact PDF — regex-based PII detection + black-box overlay,
# with an optional "flatten to image" step for genuine (non-recoverable) redaction
# ---------------------------------------------------------------------------
PII_PATTERNS = {
    "Email address": re.compile(r"[\w\.-]+@[\w\.-]+\.\w+"),
    "Phone number": re.compile(r"(\+92|0)[\s-]?3\d{2}[\s-]?\d{7}"),
    "CNIC (Pakistan ID)": re.compile(r"\d{5}-\d{7}-\d{1}"),
    "Card number": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}


def redact_pdf_ui():
    st.write("PDF mein se emails, phone numbers, CNIC aur card numbers khud dhoondo aur black box laga do.")
    st.info(
        "⚠️ Important: by default this only draws a black box **over** the text — the original "
        "text underneath can still technically be extracted by someone determined. Check "
        "**'Flatten to image'** below for genuine, non-recoverable redaction (page becomes a "
        "picture, no text layer left at all)."
    )
    file = st.file_uploader("PDF upload karo", type="pdf", key="redact")
    selected_types = st.multiselect("Kaunsi info redact karni hai?", list(PII_PATTERNS.keys()),
                                     default=list(PII_PATTERNS.keys()))
    extra_words = st.text_input("Extra names/words bhi redact karne hain? (comma separated, optional)")
    flatten = st.checkbox("Flatten to image (recommended — removes underlying text completely)", value=True)

    if file and st.button("Auto-Redact"):
        import pdfplumber

        patterns = [PII_PATTERNS[t] for t in selected_types]
        extra = [w.strip().lower() for w in extra_words.split(",") if w.strip()]
        file_bytes = file.getvalue()

        writer = PdfWriter()
        total_hits = 0

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            base_reader = PdfReader(io.BytesIO(file_bytes))
            for page_num, page in enumerate(pdf.pages):
                words = page.extract_words()
                boxes = []
                for w in words:
                    text = w["text"]
                    hit = any(p.search(text) for p in patterns) or any(e in text.lower() for e in extra)
                    if hit:
                        boxes.append((w["x0"], w["top"], w["x1"], w["bottom"]))
                        total_hits += 1

                base_page = base_reader.pages[page_num]
                if boxes:
                    page_w, page_h = float(page.width), float(page.height)
                    overlay_buf = io.BytesIO()
                    c = canvas.Canvas(overlay_buf, pagesize=(page_w, page_h))
                    c.setFillColorRGB(0, 0, 0)
                    for x0, top, x1, bottom in boxes:
                        y0 = page_h - bottom
                        y1 = page_h - top
                        c.rect(x0 - 1, y0 - 1, (x1 - x0) + 2, (y1 - y0) + 2, fill=1, stroke=0)
                    c.save()
                    overlay_buf.seek(0)
                    overlay_page = PdfReader(overlay_buf).pages[0]
                    base_page.merge_page(overlay_page)
                writer.add_page(base_page)

        buf = io.BytesIO()
        writer.write(buf)
        result_bytes = buf.getvalue()

        if flatten:
            from pdf2image import convert_from_bytes
            import img2pdf
            with st.spinner("Flattening pages to remove the text layer..."):
                images = convert_from_bytes(result_bytes, dpi=150)
                img_bytes_list = []
                for img in images:
                    b = io.BytesIO()
                    img.convert("RGB").save(b, format="PNG")
                    img_bytes_list.append(b.getvalue())
                result_bytes = img2pdf.convert(img_bytes_list)

        if total_hits == 0:
            st.warning("Koi matching sensitive info nahi mili. (Scanned/image-only PDFs ke liye pehle OCR PDF chalao.)")
        else:
            st.success(f"{total_hits} item(s) redact ho gaye!")
        st.download_button("Download redacted.pdf", result_bytes, "redacted.pdf", "application/pdf")


# ---------------------------------------------------------------------------
# Batch Processor — one operation, many files, one ZIP
# ---------------------------------------------------------------------------
def _run_single(operation, file_bytes, params):
    reader = PdfReader(io.BytesIO(file_bytes))
    writer = PdfWriter()

    if operation == "Compress":
        import pikepdf
        pdf = pikepdf.open(io.BytesIO(file_bytes))
        buf = io.BytesIO()
        pdf.save(buf, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
        return buf.getvalue()

    if operation == "Rotate":
        for page in reader.pages:
            page.rotate(params["angle"])
            writer.add_page(page)

    elif operation == "Add Watermark":
        page_w = float(reader.pages[0].mediabox.width)
        page_h = float(reader.pages[0].mediabox.height)
        wm_buf = io.BytesIO()
        c = canvas.Canvas(wm_buf, pagesize=(page_w, page_h))
        c.saveState()
        c.setFillAlpha(params["opacity"])
        c.setFont("Helvetica-Bold", 50)
        c.translate(page_w / 2, page_h / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, params["text"])
        c.restoreState()
        c.save()
        wm_buf.seek(0)
        watermark_page = PdfReader(wm_buf).pages[0]
        for page in reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)

    elif operation == "Add Page Numbers":
        total = len(reader.pages)
        page_w = float(reader.pages[0].mediabox.width)
        for i, page in enumerate(reader.pages):
            num_buf = io.BytesIO()
            c = canvas.Canvas(num_buf, pagesize=(page_w, float(page.mediabox.height)))
            label = f"{i + 1} / {total}"
            if params["position"] == "Bottom Center":
                c.drawCentredString(page_w / 2, 20, label)
            elif params["position"] == "Bottom Right":
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
    return buf.getvalue()


def batch_processor_ui():
    st.write("Ek hi operation multiple PDFs par apply karo — sab ka ZIP download mil jayega.")
    files = st.file_uploader("PDFs upload karo", type="pdf", accept_multiple_files=True, key="batch")
    operation = st.selectbox("Operation choose karo", ["Compress", "Add Watermark", "Rotate", "Add Page Numbers"])

    params = {}
    if operation == "Compress":
        pass  # pikepdf's default stream compression, no extra params needed
    elif operation == "Add Watermark":
        params["text"] = st.text_input("Watermark text", value="CONFIDENTIAL")
        params["opacity"] = st.slider("Opacity", 0.1, 1.0, 0.3)
    elif operation == "Rotate":
        params["angle"] = st.selectbox("Rotation angle", [90, 180, 270])
    elif operation == "Add Page Numbers":
        params["position"] = st.selectbox("Position", ["Bottom Center", "Bottom Right", "Bottom Left"])

    if files and st.button(f"Run {operation} on {len(files)} file(s)"):
        zip_buf = io.BytesIO()
        progress = st.progress(0)
        errors = []
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for i, f in enumerate(files):
                try:
                    result = _run_single(operation, f.getvalue(), params)
                    zf.writestr(f"{os.path.splitext(f.name)[0]}_done.pdf", result)
                except Exception as e:
                    errors.append(f"{f.name}: {e}")
                progress.progress((i + 1) / len(files))

        if errors:
            st.error("Kuch files fail ho gayeen:\n" + "\n".join(errors))
        st.success(f"{len(files) - len(errors)} file(s) processed!")
        st.download_button("Download batch_results.zip", zip_buf.getvalue(), "batch_results.zip", "application/zip")
