"""
backend.py — BizPilot FastAPI web server.

Routing & Quota-Resilience Architecture:
  1. Classify intent using ZERO-COST keyword rules.
  2. Dispatch to CHAT or BUSINESS_ANALYSIS handler.
  3. API Failover Strategy (Resilience):
     - If Gemini rate-limits us (429), it waits for the retry delay and retries.
     - If it still fails, it falls back to a high-quality Local Conversational Rule Engine
       rather than crashing. This ensures the app is NEVER frozen, and can talk
       in English, French, Arabic, and Darija even when the Gemini API is fully exhausted.
"""

import asyncio
import re
import sys
import os
import time
import pathlib
import logging

# UTF-8 stdout for emoji/Arabic on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_orig_init = httpx.Client.__init__
def _patched_init(self, *args, **kwargs):
    kwargs["verify"] = False
    _orig_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_init

_orig_async_init = httpx.AsyncClient.__init__
def _patched_async_init(self, *args, **kwargs):
    kwargs["verify"] = False
    _orig_async_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched_async_init

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────
_PROMPT_PATH = pathlib.Path("bizpilot/agents/core/prompt.md")
SYSTEM_PROMPT = (
    _PROMPT_PATH.read_text(encoding="utf-8")
    if _PROMPT_PATH.exists()
    else "You are BizPilot, an intelligent AI Business Consultant."
)

# ── Zero-cost intent classifier ───────────────────────────────────────────────
_BUSINESS_ANALYSIS_PATTERNS = [
    r"\b(swot|business\s*report|full\s*report|full\s*analysis|analyze\s*my|analyse\s*my|"
    r"analyse\s*mon|market\s*analysis|competitor\s*analysis|executive\s*report|"
    r"business\s*plan|business\s*strategy|create\s*a\s*report|generate\s*a\s*report|"
    r"تحليل\s*كامل|تقرير\s*كامل|اعمل\s*تحليل|analyse\s*compl[eè]te|fais\s*une\s*analyse)",
]

_CHAT_PATTERNS = [
    r"^(hi+|hello+|hey+|howdy|yo+)[!?. ]*$",
    r"^(bonjour|salut|bonsoir|coucou)[!?. ]*$",
    r"^(salam|ahla|marhba|labès|labes|wesh)[!?. ]*$",
    r"^(مرحبا|السلام|أهلا|هلا)[!?. ]*$",
    r"\b(do you speak|can you speak|تتكلم|تحكي|تفهم|tnajm|parles.tu|tu parles)",
    r"\b(translate|translation|ترجم|traduis|tfasser|تفسر)",
    r"\b(are you|who are you|what are you|what can you do|ما هو|ما أنت|شنوة)",
    r"\b(thank|thanks|merci|شكرا|yislem|barak)[a-z ]*$",
]


def classify_intent(message: str) -> str:
    stripped = message.strip()
    lower = stripped.lower()

    if len(stripped.split()) <= 3:
        return "CHAT"

    for pattern in _BUSINESS_ANALYSIS_PATTERNS:
        if re.search(pattern, lower, re.IGNORECASE):
            return "BUSINESS_ANALYSIS"

    for pattern in _CHAT_PATTERNS:
        if re.search(pattern, stripped, re.IGNORECASE):
            return "CHAT"

    return "CHAT"


# ── Local Rule-Based Conversational Engine (API Quota Failover) ───────────────
# When the Gemini API is exhausted, the assistant continues the conversation.
_MOCK_CONVERSATIONS = [
    # Language / Arabic
    (r"(تتكلم|تحكي|تفهم|تحدث|عربي|بالعربية|arabic)",
     "نعم، أنا أتكلم العربية، الإنجليزية، الفرنسية، والتونسية الدارجة. كيف يمكنني مساعدتك اليوم؟"),
    
    # Language / Tunisian Darija
    (r"(tounsi|tunisian|darija|تونس|تونسي|tfaserli|tnajm|تفسر)",
     "أكيد، نجّم نفسّرلك بالتونسي ونعاونك في مشروعك. قولّي شنوة تحب تعرف؟"),
    
    # Greetings / Arabic
    (r"(مرحبا|أهلي|السلام|سلام|هلا)",
     "مرحباً بك! أنا مستشارك التجاري BizPilot. كيف يمكنني مساعدتك في عملك اليوم؟"),
    
    # Greetings / Darija
    (r"\b(ahla|salam|marhba|labes|labès)\b",
     "أهلاً وسهلاً بك! أنا مستشارك BizPilot. كفاش نجم نعاونك اليوم في مشروعك؟"),
     
    # Greetings / French
    (r"\b(bonjour|salut|bonsoir|coucou)\b",
     "Bonjour ! Je suis BizPilot, votre consultant d'affaires. Comment puis-je vous aider aujourd'hui ?"),
     
    # Greetings / English
    (r"\b(hi|hello|hey|greetings)\b",
     "Hello! I am BizPilot, your AI Business Consultant. How can I help you today?"),
     
    # Business help / advice requests
    (r"\b(advice|help|business|conseil|aider|projet|مشروع|مساعدة)\b",
     "I can help you with strategy, marketing, branding, pricing, SWOT, and growth planning. "
     "Tell me more about your business domain and what challenges you are facing!"),
]

def _local_fallback_chat(user_message: str) -> str:
    """Generate high-quality conversational responses locally when Gemini is exhausted."""
    lower_message = user_message.lower()
    
    for pattern, response in _MOCK_CONVERSATIONS:
        if re.search(pattern, lower_message):
            return response
            
    # Default fallback answer if no pattern matches
    return (
        "💡 **BizPilot (Local Mode)**\n\n"
        "I am online but running in local fallback mode because my Gemini API daily quota is fully exhausted.\n\n"
        "However, I can still chat with you! Tell me: what business or startup idea are you working on?"
    )


# ── Gemini helpers ───────────────────────────────────────────────────────────

def _get_model() -> str:
    from bizpilot.config.settings import settings
    return settings.DEFAULT_LLM_MODEL


def _extract_retry_seconds(error: Exception) -> int:
    try:
        match = re.search(r"retryDelay.*?(\d+)s", str(error))
        if match:
            return min(int(match.group(1)), 60)
    except Exception:
        pass
    return 0


def _call_gemini(user_message: str, *, max_retries: int = 2) -> str:
    """Call Gemini, retrying on 429, falling back to local chat if exhausted."""
    from bizpilot.utils import get_gemini_client
    from google.genai import types

    for attempt in range(max_retries):
        try:
            client = get_gemini_client()
            response = client.models.generate_content(
                model=_get_model(),
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                ),
            )
            return response.text or "I'm here to help. What would you like to know?"
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < max_retries - 1:
                delay = _extract_retry_seconds(e)
                if delay > 0:
                    logger.warning(f"Rate limited. Waiting {delay}s before retry...")
                    time.sleep(delay)
                    continue
            logger.error(f"Gemini call failed (attempt {attempt + 1}/{max_retries}): {e}")
            break

    # If API is exhausted, call the local conversational router
    return _local_fallback_chat(user_message)


def _run_business_analysis(user_message: str) -> str:
    """Run the full orchestration pipeline, falling back to Gemini and then local chat."""
    try:
        from bizpilot.agents.core.tools import orchestrate
        result = orchestrate(user_message)
        return result.get("summary") or result.get("report") or str(result)
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        return _call_gemini(user_message)


def _process(user_message: str) -> str:
    intent = classify_intent(user_message)
    logger.info(f"Intent={intent!r} | msg={user_message[:60]!r}")
    if intent == "BUSINESS_ANALYSIS":
        return _run_business_analysis(user_message)
    return _call_gemini(user_message)


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="BizPilot API")
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    message: str


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(None, _process, req.message)
    return {"reply": reply}


@app.post("/api/report")
async def generate_report(req: ChatRequest) -> Dict[str, Any]:
    return await chat(req)
