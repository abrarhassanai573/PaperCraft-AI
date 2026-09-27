import streamlit as st
from pypdf import PdfReader, PdfWriter
import io


def protect_pdf_ui():
    st.write("Encrypt your PDF with a password.")
    file = st.file_uploader("Upload PDF", type="pdf", key="protect")
    password = st.text_input("Set a password", type="password")
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
    st.write("Remove the password from a protected PDF.")
    file = st.file_uploader("Upload PDF", type="pdf", key="unlock")
    password = st.text_input("Enter current password", type="password")
    if file and st.button("Unlock"):
        reader = PdfReader(file)
        if reader.is_encrypted:
            result = reader.decrypt(password)
            if result == 0:
                st.error("Incorrect password!")
                return
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        st.success("PDF unlocked!")
        st.download_button("Download unlocked.pdf", buf.getvalue(), "unlocked.pdf", "application/pdf")
