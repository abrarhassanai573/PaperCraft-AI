# PaperCraft AI — `tools/` folder

This folder matches the imports and UI handler names used by `app.py` in PaperCraft AI.

## Files
- `__init__.py` — package marker
- `organize.py` — merge, split, remove, extract, reorder
- `optimize.py` — compress, repair, OCR
- `convert.py` — PDF/JPG, PDF/Word, Excel/PDF, PowerPoint/PDF, PDF/Excel
- `edit.py` — rotate, watermark, page numbers
- `security.py` — password protect/unlock
- `ai_client.py` — Gemini first, Groq fallback
- `ai_tools.py` — summarizer, Markdown, chat, structured extraction

Copy the **`tools` folder itself** into the root of your GitHub repository so the structure is:

```text
PaperCraft-AI/
├── app.py
├── tools/
│   ├── __init__.py
│   ├── organize.py
│   ├── optimize.py
│   ├── convert.py
│   ├── edit.py
│   ├── security.py
│   ├── ai_client.py
│   └── ai_tools.py
```
