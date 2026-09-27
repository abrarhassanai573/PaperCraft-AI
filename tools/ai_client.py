"""
Unified AI client: Gemini (primary) with automatic Groq fallback.

Why this file exists (lessons from a past project's errors):
1. The OLD `google-generativeai` SDK + hardcoded old model names (e.g. "gemini-pro")
   breaks once Google deprecates that model -> 404 "model not found".
   FIX: use the NEW `google-genai` SDK (`from google import genai`) and a
   current model name, overridable via secrets so it never needs a code change
   when Google renames/retires a model again.
2. Silently swallowing exceptions hides the real cause (quota, bad key, blocked
   response). FIX: every failure is surfaced with the actual provider error text.
3. Single-provider = single point of failure (free-tier rate limits hit fast).
   FIX: Gemini is tried first; on ANY failure it automatically retries with Groq.
"""
import streamlit as st
import os


def _get_secret(name, default=None):
    """Safe read: st.secrets THROWS (StreamlitSecretNotFoundError) instead of
    returning a default when no secrets.toml exists at all — which is exactly
    the state of a fresh deploy before anyone has added keys. This must never
    crash app startup, so every access goes through this wrapper."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


# Current models as of Sep 2026 — override anytime via secrets.toml, no code change needed.
# NOTE: gemini-2.5-flash is scheduled for shutdown as early as Oct 16, 2026 — using
# gemini-3.5-flash instead (GA since May 2026, no shutdown date announced).
GEMINI_MODEL = _get_secret("GEMINI_MODEL", "gemini-3.5-flash")
GROQ_MODEL = _get_secret("GROQ_MODEL", "openai/gpt-oss-20b")


def _get_key(name):
    return _get_secret(name)


def _call_gemini(prompt: str, max_tokens: int) -> str:
    api_key = _get_key("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=max_tokens),
    )
    text = getattr(resp, "text", None)
    if not text:
        # response existed but had no usable text (e.g. safety block) — surface why
        reason = getattr(resp, "prompt_feedback", None) or "empty response"
        raise RuntimeError(f"Gemini returned no text ({reason})")
    return text


def _call_groq(prompt: str, max_tokens: int) -> str:
    api_key = _get_key("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    from groq import Groq

    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        max_completion_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def generate(prompt: str, max_tokens: int = 1500) -> str:
    """Try Gemini first, fall back to Groq. Raises a clear error only if BOTH fail."""
    errors = []
    for name, fn in (("Gemini", _call_gemini), ("Groq", _call_groq)):
        try:
            return fn(prompt, max_tokens)
        except Exception as e:
            errors.append(f"{name}: {e}")
    raise RuntimeError(
        "Both AI providers failed:\n" + "\n".join(errors) +
        "\n\nCheck: are GEMINI_API_KEY / GROQ_API_KEY set correctly in secrets.toml? "
        "Has the free tier quota run out?"
    )


def has_any_key() -> bool:
    return bool(_get_key("GEMINI_API_KEY") or _get_key("GROQ_API_KEY"))
