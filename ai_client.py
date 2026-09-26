import os
import streamlit as st


def _secret(name, default=None):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


def _gemini(prompt):
    key=_secret("GEMINI_API_KEY")
    if not key: raise RuntimeError("GEMINI_API_KEY is not configured.")
    from google import genai
    client=genai.Client(api_key=key)
    model=_secret("GEMINI_MODEL","gemini-2.5-flash")
    response=client.models.generate_content(model=model, contents=prompt)
    return response.text


def _groq(prompt):
    key=_secret("GROQ_API_KEY")
    if not key: raise RuntimeError("GROQ_API_KEY is not configured.")
    from groq import Groq
    client=Groq(api_key=key)
    model=_secret("GROQ_MODEL","llama-3.3-70b-versatile")
    response=client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}], temperature=0.2)
    return response.choices[0].message.content


def generate(prompt):
    errors=[]
    try: return _gemini(prompt), "Gemini"
    except Exception as e: errors.append(f"Gemini: {e}")
    try: return _groq(prompt), "Groq"
    except Exception as e: errors.append(f"Groq: {e}")
    raise RuntimeError("No AI provider succeeded. " + " | ".join(errors))
