import streamlit as st
import io
import os
import subprocess
import tempfile
import zipfile


def pdf_to_jpg_ui():
    st.write("Har PDF page ko JPG image me convert karo.")
    file = st.file_uploader("PDF upload karo", type="pdf", key="p2j")
    if file and st.button("Convert to JPG"):
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(file.getvalue())
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for i, img in enumerate(images):
                img_buf = io.BytesIO()
                img.convert("RGB").save(img_buf, format="JPEG", quality=90)
                zf.writestr(f"page_{i+1}.jpg", img_buf.getvalue())
        st.success(f"{len(images)} images generated!")
        st.download_button("Download images.zip", zip_buf.getvalue(), "images.zip", "application/zip")


def jpg_to_pdf_ui():
    st.write("Ek ya multiple JPG/PNG images ko ek PDF me combine karo.")
    files = st.file_uploader("Images upload karo", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="j2p")
    if files and st.button("Convert to PDF"):
        import img2pdf
        image_bytes = [f.getvalue() for f in files]
        pdf_bytes = img2pdf.convert(image_bytes)
        st.success(f"{len(files)} images combined into 1 PDF!")
        st.download_button("Download images.pdf", pdf_bytes, "images.pdf", "application/pdf")


def pdf_to_word_ui():
    st.write("PDF ko editable Word (.docx) me convert karo.")
    file = st.file_uploader("PDF upload karo", type="pdf", key="p2w")
    if file and st.button("Convert to Word"):
        from pdf2docx import Converter
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_in:
            tmp_in.write(file.getvalue())
            in_path = tmp_in.name
        out_path = in_path.replace(".pdf", ".docx")
        with st.spinner("Converting..."):
            cv = Converter(in_path)
            cv.convert(out_path)
            cv.close()
        with open(out_path, "rb") as f:
            result = f.read()
        os.remove(in_path)
        os.remove(out_path)
        st.success("Converted to Word!")
        st.download_button("Download converted.docx", result,
                            "converted.docx",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


def _soffice_convert_to_pdf(file, suffix):
    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, f"input{suffix}")
        with open(in_path, "wb") as f:
            f.write(file.getvalue())
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmpdir, in_path],
            check=True, timeout=120,
        )
        out_path = os.path.join(tmpdir, "input.pdf")
        with open(out_path, "rb") as f:
            return f.read()


def word_to_pdf_ui():
    st.write("Word (.docx) ko PDF me convert karo.")
    file = st.file_uploader("Word file upload karo", type=["docx", "doc"], key="w2p")
    if file and st.button("Convert to PDF"):
        with st.spinner("Converting..."):
            result = _soffice_convert_to_pdf(file, os.path.splitext(file.name)[1])
        st.success("Converted to PDF!")
        st.download_button("Download converted.pdf", result, "converted.pdf", "application/pdf")


def excel_to_pdf_ui():
    st.write("Excel (.xlsx) ko PDF me convert karo.")
    file = st.file_uploader("Excel file upload karo", type=["xlsx", "xls"], key="e2p")
    if file and st.button("Convert to PDF"):
        with st.spinner("Converting..."):
            result = _soffice_convert_to_pdf(file, os.path.splitext(file.name)[1])
        st.success("Converted to PDF!")
        st.download_button("Download converted.pdf", result, "converted.pdf", "application/pdf")


def ppt_to_pdf_ui():
    st.write("PowerPoint (.pptx) ko PDF me convert karo.")
    file = st.file_uploader("PowerPoint file upload karo", type=["pptx", "ppt"], key="pp2p")
    if file and st.button("Convert to PDF"):
        with st.spinner("Converting..."):
            result = _soffice_convert_to_pdf(file, os.path.splitext(file.name)[1])
        st.success("Converted to PDF!")
        st.download_button("Download converted.pdf", result, "converted.pdf", "application/pdf")


def pdf_to_excel_ui():
    st.write("PDF ke andar tables detect karke Excel me nikalo.")
    file = st.file_uploader("PDF upload karo", type="pdf", key="p2e")
    if file and st.button("Extract Tables to Excel"):
        import pdfplumber
        import openpyxl

        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        found = 0
        with pdfplumber.open(io.BytesIO(file.getvalue())) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                for t_idx, table in enumerate(tables):
                    found += 1
                    ws = wb.create_sheet(f"p{page_num}_t{t_idx+1}"[:31])
                    for row in table:
                        ws.append([cell if cell is not None else "" for cell in row])
        if found == 0:
            st.warning("Is PDF me koi table detect nahi hui.")
        else:
            buf = io.BytesIO()
            wb.save(buf)
            st.success(f"{found} table(s) extracted!")
            st.download_button("Download tables.xlsx", buf.getvalue(), "tables.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
