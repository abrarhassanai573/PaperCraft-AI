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

.pc-navbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 6px; margin-bottom: 8px;
    border-bottom: 1px solid #E2E8F0;
}
.pc-logo {
    font-size: 1.5rem; font-weight: 800; color: var(--text);
}
.pc-logo span { color: var(--primary); }
.pc-tagline { color: var(--muted); font-size: 0.9rem; }

.pc-section-title {
    font-size: 1.05rem; font-weight: 700; color: var(--text);
    margin: 22px 0 10px 2px; display: flex; align-items: center; gap: 8px;
}
.pc-badge {
    background: var(--accent); color: white; font-size: 0.65rem;
    padding: 2px 8px; border-radius: 999px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.03em;
}

div[data-testid="stButton"] > button {
    width: 100%; text-align: left; background: var(--card-bg);
    border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 16px 14px; font-weight: 600; color: var(--text);
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    transition: all 0.15s ease;
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

h1 { color: var(--text) !important; }
.stDownloadButton button {
    background: var(--primary) !important; color: white !important;
    border: none !important; border-radius: 8px !important; font-weight: 600 !important;
}
.stDownloadButton button:hover { background: var(--primary-dark) !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tool registry — icon, label, handler, category
# ---------------------------------------------------------------------------
TOOLS = {
    "Organize PDF": {
        "icon": "🗂️",
        "items": {
            "Merge PDF": ("📑", organize.merge_pdf_ui),
            "Split PDF": ("✂️", organize.split_pdf_ui),
            "Remove Pages": ("🗑️", organize.remove_pages_ui),
            "Extract Pages": ("📤", organize.extract_pages_ui),
            "Reorder Pages": ("🔀", organize.reorder_pages_ui),
        },
    },
    "Optimize PDF": {
        "icon": "⚡",
        "items": {
            "Compress PDF": ("📉", optimize.compress_pdf_ui),
            "Repair PDF": ("🛠️", optimize.repair_pdf_ui),
            "OCR PDF": ("🔍", optimize.ocr_pdf_ui),
        },
    },
    "Convert PDF": {
        "icon": "🔄",
        "items": {
            "PDF to JPG": ("🖼️", convert.pdf_to_jpg_ui),
            "JPG to PDF": ("📷", convert.jpg_to_pdf_ui),
            "PDF to Word": ("📝", convert.pdf_to_word_ui),
            "Word to PDF": ("📄", convert.word_to_pdf_ui),
            "Excel to PDF": ("📊", convert.excel_to_pdf_ui),
            "PowerPoint to PDF": ("📽️", convert.ppt_to_pdf_ui),
            "PDF to Excel": ("📈", convert.pdf_to_excel_ui),
        },
    },
    "Edit PDF": {
        "icon": "✏️",
        "items": {
            "Rotate PDF": ("🔁", edit.rotate_pdf_ui),
            "Add Watermark": ("💧", edit.watermark_ui),
            "Page Numbers": ("🔢", edit.page_numbers_ui),
        },
    },
    "PDF Security": {
        "icon": "🔒",
        "items": {
            "Protect PDF": ("🔐", security.protect_pdf_ui),
            "Unlock PDF": ("🔓", security.unlock_pdf_ui),
        },
    },
    "AI Intelligence": {
        "icon": "🧠",
        "badge": "Unique",
        "items": {
            "AI Summarizer": ("🧠", ai_tools.summarizer_ui),
            "PDF to Markdown": ("📋", ai_tools.pdf_to_markdown_ui),
            "Ask Your PDF": ("💬", ai_tools.chat_with_pdf_ui),
            "Smart Data Extractor": ("🎯", ai_tools.smart_extractor_ui),
        },
    },
}

if "tool" not in st.session_state:
    st.session_state.tool = None

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
    for category, data in TOOLS.items():
        badge = f'<span class="pc-badge">{data["badge"]}</span>' if "badge" in data else ""
        st.markdown(f'<div class="pc-section-title">{data["icon"]} {category} {badge}</div>',
                    unsafe_allow_html=True)
        items = list(data["items"].items())
        cols = st.columns(4)
        for i, (name, (icon, handler)) in enumerate(items):
            with cols[i % 4]:
                if st.button(f"{icon}  {name}", key=f"card_{category}_{name}"):
                    st.session_state.tool = (name, handler)
                    st.rerun()
else:
    name, handler = st.session_state.tool
    st.markdown('<div class="pc-back">', unsafe_allow_html=True)
    if st.button("← Back to all tools"):
        st.session_state.tool = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.title(name)
    handler()

st.markdown("---")
st.caption("PaperCraft AI · 100% free · open source · [GitHub](#)")
