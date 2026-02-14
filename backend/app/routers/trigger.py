"""Trigger endpoint: call LLM with Guidance to LLM.md as prompt, then execute commands in world."""

import logging
import os
import re
import time
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
        + "\n\n---\n\nTrigger: Start rescue operation. Based on the guidance above, respond with the rescue sequence and any instructions.\n\n"
        "At the end of your response, add a new line with exactly: COMMANDS:\n"
        "Then one line per command in this exact format: TELEPORT_TIAGO <robot_id> <x> <y>\n"
        "Use robot_id 1, 2, or 3 and world coordinates x, y (numbers). Example:\n"
        "COMMANDS:\nTELEPORT_TIAGO 1 4 1\nTELEPORT_TIAGO 2 5 2\nTELEPORT_TIAGO 3 6 3"
    )
    logger.info("Trigger: loading complete, calling Gemini with Guidance to LLM")
    response_text = _call_llm(prompt)
    logger.info("Trigger: received response from Gemini, parsing and executing commands")
    steps = _parse_and_execute_commands(response_text)
    logger.info("Trigger: commands executed, returning to client")
    return {"ok": True, "response": response_text, "steps": steps}


def _parse_and_execute_commands(response_text: str) -> list[str]:
    """
    Parse COMMANDS: block from LLM response (lines TELEPORT_TIAGO n x y) and
    send each to the world (supervisor) with 1 sec gap. Return list of step descriptions for UI.
    """
    steps = []
    # Find COMMANDS: block (case-insensitive)
    match = re.search(r"COMMANDS:\s*\n(.*?)(?=\n\n|\Z)", response_text, re.IGNORECASE | re.DOTALL)
    if not match:
        logger.info("Trigger: no COMMANDS block in response, skipping execution")
        return steps
    block = match.group(1).strip()
    # Parse lines: TELEPORT_TIAGO <1|2|3> <x> <y>
    pattern = re.compile(r"TELEPORT_TIAGO\s+([123])\s+([\d.-]+)\s+([\d.-]+)", re.IGNORECASE)
    commands = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            robot_id, x, y = m.group(1), float(m.group(2)), float(m.group(3))
            commands.append((int(robot_id), x, y))
    if not commands:
        return steps
    # Execute via supervisor (set its _command so Webots controller picks it up)
    try:
        from app.routers import supervisor as sup_router
    except ImportError:
        logger.warning("Trigger: could not import supervisor, skipping command execution")
        return steps
    for i, (robot_id, x, y) in enumerate(commands, 1):
        desc = f"{i}. Teleport Tiago {robot_id} to ({x}, {y})"
        steps.append(desc)
        logger.info("Trigger: %s", desc)
        sup_router._command = {
            "type": "teleport",
            "target": f"tiago{robot_id}",
            "data": {"x": x, "y": y, "z": 0.095},
        }
        time.sleep(1)
    return steps
