import streamlit as st
import pikepdf
import io
import subprocess
import tempfile
import os


def compress_pdf_ui():
    st.write("PDF ka size kam karo (images recompress + streams optimize).")
    file = st.file_uploader("PDF upload karo", type="pdf", key="compress")
    level = st.select_slider("Compression level", ["Low", "Medium", "High"], value="Medium")
    if file and st.button("Compress"):
        original_size = len(file.getvalue())
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_in:
            tmp_in.write(file.getvalue())
            in_path = tmp_in.name
        out_path = in_path.replace(".pdf", "_out.pdf")

        quality_map = {"Low": 40, "Medium": 65, "High": 85}
        try:
            # Ghostscript gives the best compression when available on the server
            gs_quality = {"Low": "/screen", "Medium": "/ebook", "High": "/printer"}[level]
            subprocess.run(
                ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
                 f"-dPDFSETTINGS={gs_quality}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
                 f"-sOutputFile={out_path}", in_path],
                check=True, timeout=120,
            )
            with open(out_path, "rb") as f:
                result = f.read()
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Fallback: pikepdf stream compression (works without ghostscript)
            pdf = pikepdf.open(in_path)
            buf = io.BytesIO()
            pdf.save(buf, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
            result = buf.getvalue()
        finally:
            for p in (in_path, out_path):
                if os.path.exists(p):
                    os.remove(p)

        new_size = len(result)
        saved = max(0, (1 - new_size / original_size) * 100) if original_size else 0
        st.success(f"Original: {original_size/1024:.0f} KB → Compressed: {new_size/1024:.0f} KB ({saved:.0f}% smaller)")
        st.download_button("Download compressed.pdf", result, "compressed.pdf", "application/pdf")


def repair_pdf_ui():
    st.write("Corrupt/damaged PDF ko repair/recover karne ki koshish karo.")
    file = st.file_uploader("PDF upload karo", type="pdf", key="repair")
    if file and st.button("Repair"):
        try:
            pdf = pikepdf.open(io.BytesIO(file.getvalue()))
            buf = io.BytesIO()
            pdf.save(buf)
            st.success("PDF repaired successfully!")
            st.download_button("Download repaired.pdf", buf.getvalue(), "repaired.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Repair fail ho gaya: {e}")


def ocr_pdf_ui():
    st.write("Scanned PDF ko searchable/selectable text wale PDF me convert karo.")
    file = st.file_uploader("PDF upload karo (scanned)", type="pdf", key="ocr")
    lang = st.selectbox("Language", ["eng", "urd", "eng+urd"], index=0)
    if file and st.button("Run OCR"):
        from pdf2image import convert_from_bytes
        import pytesseract

        with st.spinner("OCR chal raha hai, thoda time lag sakta hai..."):
            images = convert_from_bytes(file.getvalue())
            pdf_writer_bytes = []
            for img in images:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=lang)
                pdf_writer_bytes.append(pdf_bytes)

            from pypdf import PdfWriter, PdfReader
            writer = PdfWriter()
            for pb in pdf_writer_bytes:
                reader = PdfReader(io.BytesIO(pb))
                for page in reader.pages:
                    writer.add_page(page)
            buf = io.BytesIO()
            writer.write(buf)
        st.success(f"OCR complete — {len(images)} pages processed!")
        st.download_button("Download searchable.pdf", buf.getvalue(), "searchable.pdf", "application/pdf")
