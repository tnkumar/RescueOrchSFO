"""Trigger endpoint: call LLM with Guidance to LLM.md as prompt."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

# Load .env from backend/ so it works regardless of process cwd
_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trigger", tags=["Trigger"])

# Possible locations for Guidance to LLM.md (project root or cwd)
def _find_guidance_path() -> Path:
    """Resolve Guidance to LLM.md from project root or current working directory."""
    name = "Guidance to LLM.md"
    # 1. Project root = parent of backend/
    project_root = Path(__file__).resolve().parent.parent.parent
    p = project_root / name
    if p.exists():
        return p
    # 2. Cwd (e.g. when running from project root)
    p = Path.cwd() / name
    if p.exists():
        return p
    # 3. Cwd/backend (when running uvicorn from backend/)
    p = Path.cwd() / ".." / name
    if p.resolve().exists():
        return p.resolve()
    raise FileNotFoundError(f"Guidance file not found. Tried: {project_root / name}, {Path.cwd() / name}")


def _call_llm(prompt: str) -> str:
    """Call Gemini with the given prompt. Uses GEMINI_API_KEY from environment."""
    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("HACKATHON_GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it to backend/.env or your environment.")
    logger.info("GEMINI_API_KEY loaded: length=%d, starts_with_AIza=%s", len(api_key), api_key.startswith("AIza"))

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
    except ImportError:
        raise HTTPException(500, "langchain-google-genai not installed")

    model_used = "gemini-2.0-flash"
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_used,
            api_key=api_key,
            temperature=0.2,
        )
    except Exception as e:
        model_used = "gemini-1.5-flash"
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_used,
                api_key=api_key,
                temperature=0.2,
            )
        except Exception as e2:
            raise HTTPException(500, f"Failed to init Gemini: {e2}") from e

    logger.info("Calling Gemini API (model=%s)", model_used)
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        text = response.content if hasattr(response, "content") else str(response)
        logger.info("Gemini API responded successfully (response length=%d chars)", len(text))
        return text
    except Exception as e:
        logger.exception("LLM call failed")
        raise HTTPException(502, f"LLM call failed: {e}") from e


@router.post("/run")
@router.post("")
def trigger_rescue():
    """
    Run the trigger: load Guidance to LLM.md, send to LLM as prompt, return response.
    Set GEMINI_API_KEY in backend/.env or environment.
    """
    try:
        path = _find_guidance_path()
        guidance = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as e:
        logger.warning(str(e))
        raise HTTPException(503, str(e)) from e

    prompt = (
        guidance
        + "\n\n---\n\nTrigger: Start rescue operation. Based on the guidance above, respond with the rescue sequence and any instructions."
    )
    logger.info("Trigger: loading complete, calling Gemini with Guidance to LLM")
    response_text = _call_llm(prompt)
    logger.info("Trigger: received response from Gemini, returning to client")
    return {"ok": True, "response": response_text}
