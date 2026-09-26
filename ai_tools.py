import io, json
import streamlit as st
from pypdf import PdfReader
from .ai_client import generate


def _text_from_pdf(data, max_chars=50000):
    reader=PdfReader(io.BytesIO(data)); chunks=[]
    for i,p in enumerate(reader.pages):
        try: txt=p.extract_text() or ""
        except Exception: txt=""
        if txt.strip(): chunks.append(f"\n--- Page {i+1} ---\n{txt}")
        if sum(map(len,chunks))>=max_chars: break
    return "".join(chunks)[:max_chars]


def _upload(key): return st.file_uploader("Upload PDF", type="pdf", key=key)


def summarizer_ui():
    f=_upload("ai_summary_file")
    if not f:return
    if st.button("Summarize with AI", key="summary_btn"):
        text=_text_from_pdf(f.getvalue())
        if not text.strip(): st.warning("No selectable text found in this PDF."); return
        try:
            result,provider=generate("Summarize this PDF clearly. Give a short overview, key points, important facts, and action items if present.\n\n"+text)
            st.caption(f"Generated with {provider}"); st.markdown(result)
        except Exception as e: st.error(str(e))


def pdf_to_markdown_ui():
    f=_upload("ai_md_file")
    if not f:return
    if st.button("Convert to Markdown", key="md_btn"):
        text=_text_from_pdf(f.getvalue())
        if not text.strip(): st.warning("No selectable text found."); return
        try:
            result,provider=generate("Convert the following document into clean Markdown. Preserve headings, lists, tables where possible, and do not invent content.\n\n"+text)
            st.caption(f"Generated with {provider}"); st.code(result,language="markdown"); st.download_button("Download Markdown",result,file_name="document.md",mime="text/markdown")
        except Exception as e: st.error(str(e))


def chat_with_pdf_ui():
    f=_upload("ai_chat_file")
    if not f:return
    text=_text_from_pdf(f.getvalue())
    if "ai_chat_history" not in st.session_state: st.session_state.ai_chat_history=[]
    for role,msg in st.session_state.ai_chat_history:
        with st.chat_message(role): st.markdown(msg)
    q=st.chat_input("Ask a question about your PDF")
    if q:
        st.session_state.ai_chat_history.append(("user",q)); st.chat_message("user").markdown(q)
        try:
            ans,provider=generate(f"Answer the user's question only from the document below. If the answer is not in the document, say that clearly.\n\nDOCUMENT:\n{text}\n\nQUESTION:\n{q}")
            st.session_state.ai_chat_history.append(("assistant",ans)); st.chat_message("assistant").markdown(ans); st.caption(f"Generated with {provider}")
        except Exception as e: st.error(str(e))


def smart_extractor_ui():
    f=_upload("ai_extract_file")
    instruction=st.text_area("What should be extracted?", "Extract names, dates, amounts, invoice numbers, and other important fields.", key="extract_instruction")
    if not f:return
    if st.button("Extract Data", key="extract_btn"):
        text=_text_from_pdf(f.getvalue())
        if not text.strip(): st.warning("No selectable text found."); return
        try:
            result,provider=generate(f"Extract structured information from this document. Return valid JSON only. Do not invent values. Task: {instruction}\n\nDOCUMENT:\n{text}")
            cleaned=result.strip().removeprefix("```json").removesuffix("```").strip()
            try: st.json(json.loads(cleaned))
            except Exception: st.code(result,language="json")
            st.caption(f"Generated with {provider}")
        except Exception as e: st.error(str(e))
