import streamlit as st

st.set_page_config(
    page_title="PaperCraft AI — Free PDF Tools",
    page_icon="🧾",
    layout="wide",
)

from tools import organize, optimize, convert, edit, security, ai_tools

# ---------------------------------------------------------------------------
# Theme: Indigo + Teal (unique from iLovePDF's red, close to popular SaaS UIs)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
:root {
    --primary: #4F46E5;
    --primary-dark: #4338CA;
    --accent: #14B8A6;
    --bg: #F8FAFC;
    --card-bg: #FFFFFF;
    --text: #1E293B;
    --muted: #64748B;
}
.stApp { background: var(--bg); }
#MainMenu, footer, header { visibility: hidden; }

/* ---------- Navbar ---------- */
.pc-navbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 6px; margin-bottom: 6px;
    border-bottom: 1px solid #E2E8F0;
}
.pc-logo { font-size: 1.5rem; font-weight: 800; color: var(--text); }
.pc-logo span { color: var(--primary); }
.pc-tagline { color: var(--muted); font-size: 0.9rem; }

/* ---------- Hero (shown only on home) ---------- */
.pc-hero { text-align: center; padding: 18px 10px 6px; }
.pc-hero h1 { font-size: 2rem; font-weight: 800; color: var(--text); margin-bottom: 6px; }
.pc-hero p { color: var(--muted); font-size: 1rem; max-width: 720px; margin: 0 auto; }

/* ---------- Category filter pills (built from st.radio) ---------- */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    flex-direction: row; flex-wrap: wrap; justify-content: center; gap: 10px;
    margin: 18px 0 6px;
}
div[data-testid="stRadio"] label {
    background: var(--card-bg); border: 1px solid #E2E8F0; border-radius: 999px;
    padding: 7px 18px; margin: 0; cursor: pointer; transition: all 0.15s ease;
}
div[data-testid="stRadio"] label > div:first-child { display: none; }
div[data-testid="stRadio"] label p { font-size: 0.88rem; font-weight: 600; color: var(--text); margin: 0; }
div[data-testid="stRadio"] label:hover { border-color: var(--primary); }
div[data-testid="stRadio"] label:has(input:checked) { background: var(--primary); border-color: var(--primary); }
div[data-testid="stRadio"] label:has(input:checked) p { color: #fff; }

/* ---------- Section titles ---------- */
.pc-section-title {
    font-size: 1.05rem; font-weight: 700; color: var(--text);
    margin: 22px 0 10px 2px; display: flex; align-items: center; gap: 8px;
}
.pc-badge {
    background: var(--accent); color: white; font-size: 0.65rem;
    padding: 2px 8px; border-radius: 999px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.03em;
}

/* ---------- Tool cards ---------- */
.pc-card-desc {
    background: var(--card-bg); border: 1px solid #E2E8F0; border-top: none;
    border-radius: 0 0 12px 12px; padding: 6px 14px 12px; margin-top: -14px;
    font-size: 0.78rem; color: var(--muted); line-height: 1.35;
}
div[data-testid="stButton"] > button {
    width: 100%; text-align: left; background: var(--card-bg);
    border: 1px solid #E2E8F0; border-bottom: none; border-radius: 12px 12px 0 0;
    padding: 16px 14px 6px; font-weight: 700; color: var(--text); font-size: 0.95rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    transition: all 0.15s ease; border-left: 4px solid var(--cat-color, var(--primary));
}
div[data-testid="stButton"] > button:hover {
    border-color: var(--primary); box-shadow: 0 4px 12px rgba(79,70,229,0.15);
    color: var(--primary); transform: translateY(-1px);
}
.pc-back button {
    width: auto !important; background: transparent !important;
    border: none !important; color: var(--primary) !important;
    font-weight: 700 !important; padding: 4px 0 !important; box-shadow: none !important;
}
.pc-back button:hover { text-decoration: underline; transform: none; }

/* ---------- Tool page header ---------- */
.pc-tool-header { text-align: center; padding: 10px 0 20px; }
.pc-tool-icon {
    width: 56px; height: 56px; border-radius: 14px; display: flex;
    align-items: center; justify-content: center; font-size: 26px;
    margin: 0 auto 12px; background: rgba(79,70,229,0.1);
}
.pc-tool-header h1 { font-size: 1.7rem; font-weight: 800; color: var(--text); margin-bottom: 6px; }
.pc-tool-header p { color: var(--muted); font-size: 0.95rem; max-width: 600px; margin: 0 auto; }

/* ---------- File uploader — big, friendly drop zone ---------- */
div[data-testid="stFileUploader"] {
    border: 2px dashed #C7D2FE; border-radius: 16px;
    padding: 26px 20px; background: #F5F5FF; text-align: center;
}
div[data-testid="stFileUploader"] section { background: transparent; border: none; }
div[data-testid="stFileUploader"] button {
    background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 700 !important; padding: 10px 26px !important;
}

h1 { color: var(--text) !important; }
.stDownloadButton button {
    background: var(--primary) !important; color: white !important;
    border: none !important; border-radius: 8px !important; font-weight: 600 !important;
}
.stDownloadButton button:hover { background: var(--primary-dark) !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tool registry — icon, label, description, handler, per-category color
# ---------------------------------------------------------------------------
CATEGORY_COLORS = {
    "Organize PDF": "#4F46E5",
    "Optimize PDF": "#14B8A6",
    "Convert PDF": "#F59E0B",
    "Edit PDF": "#EC4899",
    "PDF Security": "#3B82F6",
    "AI Intelligence": "#8B5CF6",
}

TOOLS = {
    "Organize PDF": {
        "icon": "🗂️",
        "items": {
            "Merge PDF": ("📑", organize.merge_pdf_ui,
                          "Combine PDFs in the order you want with the easiest PDF merger available."),
            "Split PDF": ("✂️", organize.split_pdf_ui,
                          "Separate one page or a whole set into independent PDF files."),
            "Remove Pages": ("🗑️", organize.remove_pages_ui,
                             "Delete the pages you don't need from your PDF in a few clicks."),
            "Extract Pages": ("📤", organize.extract_pages_ui,
                              "Pull out just the pages you need into a brand-new PDF."),
            "Reorder Pages": ("🔀", organize.reorder_pages_ui,
                              "Rearrange your PDF's pages into any order you like."),
        },
    },
    "Optimize PDF": {
        "icon": "⚡",
        "items": {
            "Compress PDF": ("📉", optimize.compress_pdf_ui,
                             "Reduce file size while optimizing for maximal PDF quality."),
            "Repair PDF": ("🛠️", optimize.repair_pdf_ui,
                          "Repair a damaged PDF and recover data from a corrupt file."),
            "OCR PDF": ("🔍", optimize.ocr_pdf_ui,
                       "Turn a scanned PDF into a searchable, selectable document."),
        },
    },
    "Convert PDF": {
        "icon": "🔄",
        "items": {
            "PDF to JPG": ("🖼️", convert.pdf_to_jpg_ui, "Convert each PDF page into a high-quality JPG image."),
            "JPG to PDF": ("📷", convert.jpg_to_pdf_ui, "Combine one or more images into a single PDF file."),
            "PDF to Word": ("📝", convert.pdf_to_word_ui, "Turn your PDF into an easy-to-edit Word document."),
            "Word to PDF": ("📄", convert.word_to_pdf_ui, "Make DOC and DOCX files easy to share by converting to PDF."),
            "Excel to PDF": ("📊", convert.excel_to_pdf_ui, "Make Excel spreadsheets easy to read by converting to PDF."),
            "PowerPoint to PDF": ("📽️", convert.ppt_to_pdf_ui, "Turn your slideshows into easy-to-share PDFs."),
            "PDF to Excel": ("📈", convert.pdf_to_excel_ui, "Pull tables straight out of a PDF into an Excel file."),
        },
    },
    "Edit PDF": {
        "icon": "✏️",
        "items": {
            "Rotate PDF": ("🔁", edit.rotate_pdf_ui, "Rotate one or every page of your PDF to the angle you need."),
            "Add Watermark": ("💧", edit.watermark_ui, "Stamp text over your PDF pages to mark ownership."),
            "Page Numbers": ("🔢", edit.page_numbers_ui, "Add page numbers into your PDF with just a few clicks."),
        },
    },
    "PDF Security": {
        "icon": "🔒",
        "items": {
            "Protect PDF": ("🔐", security.protect_pdf_ui, "Encrypt your PDF with a password to prevent unauthorized access."),
            "Unlock PDF": ("🔓", security.unlock_pdf_ui, "Remove password security so you're free to use your PDF as you want."),
        },
    },
    "AI Intelligence": {
        "icon": "🧠",
        "badge": "Unique",
        "items": {
            "AI Summarizer": ("🧠", ai_tools.summarizer_ui, "Quickly generate concise summaries from any document."),
            "PDF to Markdown": ("📋", ai_tools.pdf_to_markdown_ui, "Turn PDFs into clean Markdown — perfect for notes and docs."),
            "Ask Your PDF": ("💬", ai_tools.chat_with_pdf_ui, "Chat with your document and get instant, grounded answers."),
            "Smart Data Extractor": ("🎯", ai_tools.smart_extractor_ui, "Pull structured fields from invoices and forms into JSON."),
        },
    },
}

if "tool" not in st.session_state:
    st.session_state.tool = None
if "category" not in st.session_state:
    st.session_state.category = "All"

# ---------------------------------------------------------------------------
# Navbar
# ---------------------------------------------------------------------------
st.markdown("""
<div class="pc-navbar">
    <div>
        <div class="pc-logo">Paper<span>Craft</span> AI</div>
        <div class="pc-tagline">Free, professional PDF tools — with AI superpowers</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Home grid OR active tool
# ---------------------------------------------------------------------------
if st.session_state.tool is None:
    st.markdown("""
    <div class="pc-hero">
        <h1>Every tool you need to work with PDFs in one place</h1>
        <p>Merge, split, compress, convert, edit and unlock PDFs — 100% free.
        Plus AI tools you won't find on other PDF sites.</p>
    </div>
    """, unsafe_allow_html=True)

    categories = ["All"] + list(TOOLS.keys())
    selected = st.radio("Filter tools", categories, horizontal=True,
                         label_visibility="collapsed", key="category")

    shown = TOOLS.items() if selected == "All" else [(selected, TOOLS[selected])]

    for category, data in shown:
        badge = f'<span class="pc-badge">{data["badge"]}</span>' if "badge" in data else ""
        st.markdown(f'<div class="pc-section-title">{data["icon"]} {category} {badge}</div>',
                    unsafe_allow_html=True)
        color = CATEGORY_COLORS.get(category, "#4F46E5")
        st.markdown(f'<style>div[data-testid="stButton"] > button {{ --cat-color: {color}; }}</style>',
                    unsafe_allow_html=True)
        items = list(data["items"].items())
        cols = st.columns(4)
        for i, (name, (icon, handler, desc)) in enumerate(items):
            with cols[i % 4]:
                if st.button(f"{icon}  {name}", key=f"card_{category}_{name}"):
                    st.session_state.tool = (name, icon, handler)
                    st.rerun()
                st.markdown(f'<div class="pc-card-desc">{desc}</div>', unsafe_allow_html=True)
else:
    name, icon, handler = st.session_state.tool
    st.markdown('<div class="pc-back">', unsafe_allow_html=True)
    if st.button("← Back to all tools"):
        st.session_state.tool = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="pc-tool-header">
        <div class="pc-tool-icon">{icon}</div>
        <h1>{name}</h1>
    </div>
    """, unsafe_allow_html=True)

    handler()

st.markdown("---")
st.caption("PaperCraft AI · 100% free · open source · [GitHub](#)")
