# 📄 PaperCraft AI — Free & Open PDF Tools

A free, open-source alternative to iLovePDF — built with Streamlit + Python.
All core tools run with **no API key required**. AI-powered tools (marked 🧠)
are unique features not found in iLovePDF, and use your own free **Gemini**
and/or **Groq** API key (Gemini tried first, Groq is an automatic fallback —
so one provider's rate limit doesn't take the feature down).

Model names are **not hardcoded** without an override path — see
`GEMINI_MODEL` / `GROQ_MODEL` in `secrets.toml.example`. If Google or Groq
retire the default model later, just change the secret, no code edit needed.

## ✅ Features

**Organize** — Merge, Split, Remove Pages, Extract Pages, Reorder Pages
**Optimize** — Compress, Repair, OCR (scanned → searchable)
**Convert** — PDF↔JPG, PDF↔Word, Excel→PDF, PowerPoint→PDF, PDF→Excel (tables)
**Edit** — Rotate, Watermark, Page Numbers
**Security** — Protect (password), Unlock
**🧠 AI Intelligence (unique, beyond iLovePDF)**
- AI Summarizer
- PDF → Markdown
- Ask Your PDF (chat with your document)
- Smart Data Extractor (invoices/forms → JSON)

## 🗺️ Roadmap (not yet built)
- [ ] Crop PDF / Redact PDF / Compare PDF versions
- [ ] E-signatures
- [ ] Fillable PDF forms
- [ ] Urdu/Roman-Urdu OCR + translation (differentiator)
- [ ] Batch/workflow automation (chain multiple tools)
- [ ] Fully client-side mode for small tools (privacy + speed)

## 🚀 Run locally

```bash
git clone https://github.com/abrarhassanai573/papercraft-ai.git
cd papercraft-ai
pip install -r requirements.txt
streamlit run app.py
```

> Word/Excel/PPT conversion needs LibreOffice installed locally (`soffice`).
> OCR needs `tesseract-ocr` and `poppler-utils` installed.

## ☁️ Deploy free on Streamlit Community Cloud

1. Push this repo to your GitHub account (see below).
2. Go to https://share.streamlit.io → **New app** → select your repo, branch `main`, file `app.py`.
3. Streamlit Cloud automatically installs `requirements.txt` (Python) and
   `packages.txt` (system packages: LibreOffice, Tesseract, Poppler, etc.).
4. (Optional, for AI tools) In **App settings → Secrets**, paste contents of
   `.streamlit/secrets.toml.example` with your real `GEMINI_API_KEY` and/or
   `GROQ_API_KEY`.
   - Get a free Gemini key: https://aistudio.google.com/apikey
   - Get a free Groq key: https://console.groq.com/keys
5. Deploy — you get a free public URL like `yourapp.streamlit.app`.

## 📤 Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: PaperCraft AI"
git branch -M main
git remote add origin https://github.com/abrarhassanai573/papercraft-ai.git
git push -u origin main
```

## 🧱 Project structure

```
papercraft-ai/
├── app.py                 # Main Streamlit app (navigation)
├── tools/
│   ├── organize.py        # Merge, split, remove, extract, reorder
│   ├── optimize.py         # Compress, repair, OCR
│   ├── convert.py          # PDF<->JPG, PDF<->Word/Excel/PPT
│   ├── edit.py             # Rotate, watermark, page numbers
│   ├── security.py         # Protect, unlock
│   ├── ai_client.py        # Gemini + Groq unified client with fallback
│   └── ai_tools.py         # Summarizer, markdown, chatbot, extractor
├── requirements.txt
├── packages.txt            # apt dependencies for Streamlit Cloud
└── .streamlit/secrets.toml.example
```
