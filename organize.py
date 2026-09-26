import io
from pypdf import PdfReader, PdfWriter
import streamlit as st


def _download(data, filename, label="Download PDF"):
    st.download_button(label, data=data, file_name=filename, mime="application/pdf")


def merge_pdf_ui():
    files = st.file_uploader("Upload 2 or more PDF files", type="pdf", accept_multiple_files=True, key="merge_files")
    if st.button("Merge PDFs", key="merge_btn", disabled=len(files) < 2):
        writer = PdfWriter()
        try:
            for f in files:
                for page in PdfReader(f).pages:
                    writer.add_page(page)
            out = io.BytesIO(); writer.write(out)
            _download(out.getvalue(), "merged.pdf")
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
            indices = _parse_ranges(pages, len(reader.pages))
            writer = PdfWriter()
            for i in indices: writer.add_page(reader.pages[i])
            out=io.BytesIO(); writer.write(out)
            _download(out.getvalue(), "split.pdf")
        except Exception as e: st.error(str(e))


def _parse_ranges(spec, total):
    result=[]
    for part in spec.replace(" ", "").split(","):
        if not part: continue
        if "-" in part:
            a,b=part.split("-",1); start,end=int(a),int(b)
            if start>end: start,end=end,start
            result.extend(range(start-1,end))
        else: result.append(int(part)-1)
    if not result or any(i<0 or i>=total for i in result): raise ValueError("Invalid page range.")
    return result


def remove_pages_ui():
    f=st.file_uploader("Upload a PDF", type="pdf", key="remove_file")
    if not f:return
    reader=PdfReader(f); st.caption(f"Pages: {len(reader.pages)}")
    spec=st.text_input("Pages to remove (e.g. 2,4-6)", key="remove_pages")
    if st.button("Remove Pages", key="remove_btn"):
        try:
            remove=set(_parse_ranges(spec,len(reader.pages))); writer=PdfWriter()
            for i,p in enumerate(reader.pages):
                if i not in remove: writer.add_page(p)
            out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"pages_removed.pdf")
        except Exception as e: st.error(str(e))


def extract_pages_ui():
    f=st.file_uploader("Upload a PDF", type="pdf", key="extract_file")
    if not f:return
    reader=PdfReader(f); st.caption(f"Pages: {len(reader.pages)}")
    spec=st.text_input("Pages to extract (e.g. 1,3-5)", key="extract_pages")
    if st.button("Extract Pages", key="extract_btn"):
        try:
            writer=PdfWriter()
            for i in _parse_ranges(spec,len(reader.pages)): writer.add_page(reader.pages[i])
            out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"extracted_pages.pdf")
        except Exception as e: st.error(str(e))


def reorder_pages_ui():
    f=st.file_uploader("Upload a PDF", type="pdf", key="reorder_file")
    if not f:return
    reader=PdfReader(f); total=len(reader.pages)
    st.info(f"Enter the new order using page numbers 1–{total}. Example: 3,1,2")
    order=st.text_input("New page order", value=",".join(map(str,range(1,total+1))), key="order_pages")
    if st.button("Reorder Pages", key="reorder_btn"):
        try:
            indices=[int(x.strip())-1 for x in order.split(",") if x.strip()]
            if sorted(indices)!=list(range(total)): raise ValueError("Use every page exactly once.")
            writer=PdfWriter()
            for i in indices: writer.add_page(reader.pages[i])
            out=io.BytesIO(); writer.write(out); _download(out.getvalue(),"reordered.pdf")
        except Exception as e: st.error(str(e))
