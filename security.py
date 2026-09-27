import streamlit as st
from pypdf import PdfReader, PdfWriter
import io


def protect_pdf_ui():
    st.write("PDF par password laga ke encrypt karo.")
    file = st.file_uploader("PDF upload karo", type="pdf", key="protect")
    password = st.text_input("Password set karo", type="password")
    if file and password and st.button("Protect"):
        reader = PdfReader(file)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        buf = io.BytesIO()
        writer.write(buf)
        st.success("PDF protected with password!")
        st.download_button("Download protected.pdf", buf.getvalue(), "protected.pdf", "application/pdf")


def unlock_pdf_ui():
    st.write("Password-protected PDF se password remove karo.")
    file = st.file_uploader("PDF upload karo", type="pdf", key="unlock")
    password = st.text_input("Current password daalo", type="password")
    if file and st.button("Unlock"):
        reader = PdfReader(file)
        if reader.is_encrypted:
            result = reader.decrypt(password)
            if result == 0:
                st.error("Galat password!")
                return
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        st.success("PDF unlocked!")
        st.download_button("Download unlocked.pdf", buf.getvalue(), "unlocked.pdf", "application/pdf")
