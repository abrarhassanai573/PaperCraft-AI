import io, os, shutil, subprocess, tempfile
from pathlib import Path
from pypdf import PdfReader, PdfWriter
import streamlit as st


def _download(data, filename, mime):
    st.download_button("Download", data=data, file_name=filename, mime=mime)


def pdf_to_jpg_ui():
    f=st.file_uploader("Upload PDF", type="pdf", key="pdf_jpg_file")
    if not f:return
    if st.button("Convert to JPG", key="pdf_jpg_btn"):
        try:
            from pdf2image import convert_from_bytes
            pages=convert_from_bytes(f.getvalue(), dpi=150)
            if len(pages)==1:
                b=io.BytesIO(); pages[0].convert("RGB").save(b,"JPEG",quality=92); _download(b.getvalue(),"page-1.jpg","image/jpeg")
            else:
                import zipfile
                z=io.BytesIO()
                with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as zz:
                    for i,p in enumerate(pages,1):
                        b=io.BytesIO(); p.convert("RGB").save(b,"JPEG",quality=92); zz.writestr(f"page-{i}.jpg",b.getvalue())
                _download(z.getvalue(),"pdf-pages.zip","application/zip")
        except Exception as e: st.error(f"Conversion failed: {e}")


def jpg_to_pdf_ui():
    files=st.file_uploader("Upload JPG/PNG images", type=["jpg","jpeg","png"], accept_multiple_files=True, key="jpg_pdf_files")
    if not files:return
    if st.button("Create PDF", key="jpg_pdf_btn"):
        try:
            from PIL import Image
            imgs=[Image.open(f).convert("RGB") for f in files]
            out=io.BytesIO(); imgs[0].save(out,format="PDF",save_all=True,append_images=imgs[1:]); _download(out.getvalue(),"images.pdf","application/pdf")
        except Exception as e: st.error(str(e))


def _run_libreoffice(src_bytes, input_name, output_ext):
    with tempfile.TemporaryDirectory() as td:
        src=Path(td)/input_name; src.write_bytes(src_bytes)
        outdir=Path(td)/"out"; outdir.mkdir()
        subprocess.run(["soffice","--headless","--convert-to",output_ext,"--outdir",str(outdir),str(src)], check=True, capture_output=True, text=True, timeout=120)
        result=outdir/(src.stem+"."+output_ext.split(":")[0])
        if not result.exists():
            matches=list(outdir.iterdir())
            if not matches: raise RuntimeError("LibreOffice produced no output.")
            result=matches[0]
        return result.read_bytes()


def pdf_to_word_ui():
    f=st.file_uploader("Upload PDF", type="pdf", key="pdf_word_file")
    if not f:return
    if st.button("Convert to Word", key="pdf_word_btn"):
        try:
            from pdf2docx import Converter
            with tempfile.TemporaryDirectory() as td:
                src=Path(td)/"input.pdf"; dst=Path(td)/"output.docx"; src.write_bytes(f.getvalue())
                cv=Converter(str(src)); cv.convert(str(dst)); cv.close(); _download(dst.read_bytes(),"converted.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as e: st.error(f"PDF to Word failed: {e}")


def word_to_pdf_ui():
    f=st.file_uploader("Upload Word document", type=["doc","docx"], key="word_pdf_file")
    if not f:return
    if st.button("Convert to PDF", key="word_pdf_btn"):
        try: _download(_run_libreoffice(f.getvalue(),f.name,"pdf"),"converted.pdf","application/pdf")
        except Exception as e: st.error(f"Word to PDF failed. LibreOffice is required: {e}")


def excel_to_pdf_ui():
    f=st.file_uploader("Upload Excel workbook", type=["xls","xlsx"], key="excel_pdf_file")
    if not f:return
    if st.button("Convert to PDF", key="excel_pdf_btn"):
        try: _download(_run_libreoffice(f.getvalue(),f.name,"pdf"),"converted.pdf","application/pdf")
        except Exception as e: st.error(f"Excel to PDF failed. LibreOffice is required: {e}")


def ppt_to_pdf_ui():
    f=st.file_uploader("Upload PowerPoint", type=["ppt","pptx"], key="ppt_pdf_file")
    if not f:return
    if st.button("Convert to PDF", key="ppt_pdf_btn"):
        try: _download(_run_libreoffice(f.getvalue(),f.name,"pdf"),"converted.pdf","application/pdf")
        except Exception as e: st.error(f"PowerPoint to PDF failed. LibreOffice is required: {e}")


def pdf_to_excel_ui():
    f=st.file_uploader("Upload PDF containing tables", type="pdf", key="pdf_excel_file")
    if not f:return
    if st.button("Extract Tables to Excel", key="pdf_excel_btn"):
        try:
            import pdfplumber
            from openpyxl import Workbook
            wb=Workbook(); ws=wb.active; ws.title="Extracted Tables"
            row=1; found=0
            with pdfplumber.open(io.BytesIO(f.getvalue())) as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables() or []:
                        found+=1
                        for r in table:
                            for c,val in enumerate(r,1): ws.cell(row=row,column=c,value=val)
                            row+=1
                        row+=1
            if not found: st.warning("No tables were detected."); return
            out=io.BytesIO(); wb.save(out); _download(out.getvalue(),"extracted_tables.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e: st.error(f"PDF to Excel failed: {e}")
