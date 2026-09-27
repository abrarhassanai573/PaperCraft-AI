import streamlit as st
from pypdf import PdfReader, PdfWriter
import io


def merge_pdf_ui():
    st.write("Combine multiple PDFs in the order you want.")
    files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if files and len(files) >= 2:
        order = st.multiselect(
            "Set the order (the sequence you select here will be the final order)",
            options=[f.name for f in files],
            default=[f.name for f in files],
        )
        if st.button("Merge PDF"):
            writer = PdfWriter()
            name_to_file = {f.name: f for f in files}
            for name in order:
                reader = PdfReader(name_to_file[name])
                for page in reader.pages:
                    writer.add_page(page)
            buf = io.BytesIO()
            writer.write(buf)
            st.success(f"Merged {len(order)} files successfully!")
            st.download_button("Download merged.pdf", buf.getvalue(), "merged.pdf", "application/pdf")
    elif files:
        st.info("Upload at least 2 files to merge.")


def split_pdf_ui():
    st.write("Split a PDF into multiple files (each page becomes a separate file).")
    file = st.file_uploader("Upload PDF", type="pdf")
    if file:
        reader = PdfReader(file)
        total = len(reader.pages)
        st.caption(f"Total pages: {total}")
        if st.button("Split into individual pages"):
            import zipfile
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as zf:
                for i in range(total):
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    page_buf = io.BytesIO()
                    writer.write(page_buf)
                    zf.writestr(f"page_{i+1}.pdf", page_buf.getvalue())
            st.success(f"Split into {total} files!")
            st.download_button("Download ZIP", zip_buf.getvalue(), "split_pages.zip", "application/zip")


def _parse_page_ranges(text, total):
    """'1-3,5,7-9' -> sorted set of 0-indexed page numbers"""
    pages = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-")
            pages.update(range(int(a) - 1, int(b)))
        else:
            pages.add(int(part) - 1)
    return sorted(p for p in pages if 0 <= p < total)


def remove_pages_ui():
    st.write("Remove specific pages from a PDF.")
    file = st.file_uploader("Upload PDF", type="pdf", key="remove")
    if file:
        reader = PdfReader(file)
        total = len(reader.pages)
        st.caption(f"Total pages: {total}")
        ranges = st.text_input("Pages to remove (e.g. 2,4-6)")
        if st.button("Remove Pages") and ranges:
            remove_set = set(_parse_page_ranges(ranges, total))
            writer = PdfWriter()
            for i, page in enumerate(reader.pages):
                if i not in remove_set:
                    writer.add_page(page)
            buf = io.BytesIO()
            writer.write(buf)
            st.success(f"Removed {len(remove_set)} pages!")
            st.download_button("Download result.pdf", buf.getvalue(), "result.pdf", "application/pdf")


def extract_pages_ui():
    st.write("Extract specific pages into a brand-new PDF.")
    file = st.file_uploader("Upload PDF", type="pdf", key="extract")
    if file:
        reader = PdfReader(file)
        total = len(reader.pages)
        st.caption(f"Total pages: {total}")
        ranges = st.text_input("Pages to extract (e.g. 1-3,5)")
        if st.button("Extract Pages") and ranges:
            keep = _parse_page_ranges(ranges, total)
            writer = PdfWriter()
            for i in keep:
                writer.add_page(reader.pages[i])
            buf = io.BytesIO()
            writer.write(buf)
            st.success(f"Extracted {len(keep)} pages!")
            st.download_button("Download extracted.pdf", buf.getvalue(), "extracted.pdf", "application/pdf")


def reorder_pages_ui():
    st.write("Change the order of your PDF's pages.")
    file = st.file_uploader("Upload PDF", type="pdf", key="reorder")
    if file:
        reader = PdfReader(file)
        total = len(reader.pages)
        st.caption(f"Total pages: {total}. Enter the new order, comma-separated (e.g. 3,1,2,4)")
        order_text = st.text_input("New order", value=",".join(str(i + 1) for i in range(total)))
        if st.button("Reorder"):
            new_order = [int(x.strip()) - 1 for x in order_text.split(",") if x.strip()]
            writer = PdfWriter()
            for i in new_order:
                writer.add_page(reader.pages[i])
            buf = io.BytesIO()
            writer.write(buf)
            st.success("Pages reordered!")
            st.download_button("Download reordered.pdf", buf.getvalue(), "reordered.pdf", "application/pdf")
