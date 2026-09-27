import streamlit as st
import pdfplumber
import io

from tools import ai_client


def _extract_text(file_bytes):
    text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    return "\n\n".join(text)


def _extract_text_with_pages(file_bytes):
    """Same as _extract_text but tags each page so the AI can cite where it found something."""
    chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            chunks.append(f"[Page {i}]\n{page.extract_text() or ''}")
    return "\n\n".join(chunks)


def _require_key():
    if not ai_client.has_any_key():
        st.warning(
            "AI features need an API key. Add `GEMINI_API_KEY` and/or `GROQ_API_KEY` "
            "(add both to get automatic fallback) in `.streamlit/secrets.toml` — see the README."
        )
        return False
    return True


def _safe_generate(prompt, max_tokens=1500):
    try:
        return ai_client.generate(prompt, max_tokens)
    except Exception as e:
        st.error(str(e))
        return None


def summarizer_ui():
    st.write("Generate an AI-powered, concise summary of your PDF.")
    file = st.file_uploader("Upload PDF", type="pdf", key="sum")
    length = st.select_slider("Summary length", ["Short", "Medium", "Detailed"], value="Medium")
    if file and st.button("Summarize"):
        if not _require_key():
            return
        with st.spinner("Reading & summarizing..."):
            text = _extract_text(file.getvalue())[:50000]
            summary = _safe_generate(
                f"Summarize the following document ({length.lower()} length). "
                f"Give clear key points:\n\n{text}",
                max_tokens=1000,
            )
        if summary:
            st.markdown(summary)
            st.download_button("Download summary.txt", summary, "summary.txt")


def pdf_to_markdown_ui():
    st.write("Convert a PDF into clean Markdown (headings, tables, and lists preserved).")
    file = st.file_uploader("Upload PDF", type="pdf", key="md")
    if file and st.button("Convert to Markdown"):
        if not _require_key():
            return
        with st.spinner("Converting..."):
            text = _extract_text(file.getvalue())[:80000]
            md = _safe_generate(
                f"Convert this document's content into clean, well-structured Markdown "
                f"(preserve headings, lists, tables where possible). Return only the Markdown:\n\n{text}",
                max_tokens=4000,
            )
        if md:
            st.code(md, language="markdown")
            st.download_button("Download converted.md", md, "converted.md")


def chat_with_pdf_ui():
    st.write("Upload a PDF and ask questions about it — answers will reference the page they came from.")
    file = st.file_uploader("Upload PDF", type="pdf", key="chat")
    if file:
        if "chat_pdf_text" not in st.session_state or st.session_state.get("chat_pdf_name") != file.name:
            st.session_state.chat_pdf_text = _extract_text_with_pages(file.getvalue())[:60000]
            st.session_state.chat_pdf_name = file.name
            st.session_state.chat_history = []

        for role, msg in st.session_state.get("chat_history", []):
            st.chat_message(role).write(msg)

        question = st.chat_input("Type your question...")
        if question:
            if not _require_key():
                return
            st.session_state.chat_history.append(("user", question))
            st.chat_message("user").write(question)
            with st.spinner("Thinking..."):
                answer = _safe_generate(
                    f"Document (each section is tagged [Page N]):\n{st.session_state.chat_pdf_text}\n\n"
                    f"Question: {question}\n"
                    f"Answer based only on the document above. If your answer relies on a specific "
                    f"part of the document, mention the page number in parentheses, e.g. (Page 3).",
                    max_tokens=800,
                )
            if answer:
                st.session_state.chat_history.append(("assistant", answer))
                st.chat_message("assistant").write(answer)


def smart_extractor_ui():
    st.write("Extract structured data from invoices, forms, or ID documents as JSON.")
    file = st.file_uploader("Upload PDF", type="pdf", key="extract_ai")
    fields = st.text_input("Which fields do you need? (comma separated)",
                            value="name, date, total amount, invoice number")
    if file and st.button("Extract Data"):
        if not _require_key():
            return
        with st.spinner("Extracting..."):
            text = _extract_text(file.getvalue())[:30000]
            result = _safe_generate(
                f"Extract these fields as JSON only, no explanation: {fields}\n\nDocument:\n{text}",
                max_tokens=800,
            )
        if result:
            st.code(result, language="json")
            st.download_button("Download data.json", result, "data.json")


def compare_pdf_ui():
    st.write("Upload two PDF versions and AI will explain, in plain language, what actually changed.")
    col1, col2 = st.columns(2)
    with col1:
        file_a = st.file_uploader("First PDF (older version)", type="pdf", key="cmp_a")
    with col2:
        file_b = st.file_uploader("Second PDF (newer version)", type="pdf", key="cmp_b")

    if file_a and file_b and st.button("Compare"):
        if not _require_key():
            return
        with st.spinner("Reading both documents..."):
            text_a = _extract_text(file_a.getvalue())[:25000]
            text_b = _extract_text(file_b.getvalue())[:25000]
            result = _safe_generate(
                "Compare Document A and Document B below. List, in plain language and as bullet "
                "points: (1) what was added, (2) what was removed, (3) what was changed/reworded. "
                "Ignore trivial formatting differences and focus on meaningful content changes.\n\n"
                f"--- Document A ---\n{text_a}\n\n--- Document B ---\n{text_b}",
                max_tokens=1200,
            )
        if result:
            st.markdown(result)
            st.download_button("Download comparison.txt", result, "comparison.txt")


def translate_pdf_ui():
    st.write("Translate a PDF's text into any language (Urdu, Roman Urdu, English, Arabic, etc.).")
    st.caption("Have a scanned/image-only Urdu PDF? Run the **OCR PDF** tool first "
               "(language: Urdu or eng+urd), then upload that output here.")
    file = st.file_uploader("Upload PDF", type="pdf", key="translate")
    target = st.selectbox(
        "Target language",
        ["Urdu", "Roman Urdu (Urdu written in English letters)", "English", "Arabic", "Punjabi", "Other (type below)"],
    )
    custom_lang = ""
    if target == "Other (type below)":
        custom_lang = st.text_input("Type a language")
    if file and st.button("Translate"):
        if not _require_key():
            return
        lang = custom_lang if target == "Other (type below)" else target
        with st.spinner("Translating..."):
            text = _extract_text(file.getvalue())[:40000]
            result = _safe_generate(
                f"Translate the following document into {lang}. Keep the meaning accurate and the "
                f"structure (headings, lists, paragraphs) as close to the original as possible. "
                f"Return only the translated text:\n\n{text}",
                max_tokens=4000,
            )
        if result:
            st.markdown(result)
            st.download_button("Download translated.txt", result, "translated.txt")
