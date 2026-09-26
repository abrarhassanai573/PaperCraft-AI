import io
from pypdf import PdfReader, PdfWriter
import streamlit as st


def _download(data, filename):
    st.download_button("Download PDF", data=data, file_name=filename, mime="application/pdf")


def protect_pdf_ui():
    f=st.file_uploader("Upload PDF", type="pdf", key="protect_file")
    pw=st.text_input("Password", type="password", key="protect_pw")
    if not f:return
    if st.button("Protect PDF", key="protect_btn"):
        if not pw: st.warning("Enter a password."); return
        try:
            reader=PdfReader(f); writer=PdfWriter()
            for p in reader.pages: writer.add_page(p)
            writer.encrypt(pw); out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"protected.pdf")
        except Exception as e: st.error(str(e))


def unlock_pdf_ui():
    f=st.file_uploader("Upload protected PDF", type="pdf", key="unlock_file")
    pw=st.text_input("Current password", type="password", key="unlock_pw")
    if not f:return
    if st.button("Unlock PDF", key="unlock_btn"):
        try:
            reader=PdfReader(f)
            if reader.is_encrypted and reader.decrypt(pw)==0: raise ValueError("Incorrect password.")
            writer=PdfWriter()
            for p in reader.pages: writer.add_page(p)
            out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"unlocked.pdf")
        except Exception as e: st.error(f"Unlock failed: {e}")
