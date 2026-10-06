"""A minimal, production-shaped LLM agent service.

This is the thing the kit deploys: a small FastAPI app that wraps an LLM call
behind a clean HTTP API, with the operational pieces a real deployment needs —
health/readiness probes, structured logging, a request timeout, and a graceful
fallback when no API key is configured (so it runs locally with zero setup).

Swap the `call_llm` body for your provider; everything else is deployment-ready.
"""
from __future__ import annotations

import logging
import os
import sys
import time

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","msg":"%(message)s"}',
    stream=sys.stdout,
)
log = logging.getLogger("agent")

APP_VERSION = os.getenv("APP_VERSION", "dev")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")       # injected from a k8s Secret
MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-5")

app = FastAPI(title="agent-to-prod", version=APP_VERSION)


class InvokeRequest(BaseModel):
    prompt: str
    max_tokens: int = 512


class InvokeResponse(BaseModel):
    model: str
    output: str
    stubbed: bool


@app.get("/healthz")
def healthz() -> dict:
    """Liveness: the process is up."""
    return {"status": "ok", "version": APP_VERSION}


@app.get("/readyz")
def readyz() -> dict:
    """Readiness: ready to serve. Report whether a real key is configured."""
    return {"status": "ready", "llm_configured": bool(LLM_API_KEY)}


@app.post("/invoke", response_model=InvokeResponse)
def invoke(req: InvokeRequest) -> InvokeResponse:
    start = time.time()
    output, stubbed = call_llm(req.prompt, req.max_tokens)
    log.info(
        "invoke model=%s stubbed=%s dur_ms=%d",
        MODEL, stubbed, int((time.time() - start) * 1000),
    )
    return InvokeResponse(model=MODEL, output=output, stubbed=stubbed)


def call_llm(prompt: str, max_tokens: int) -> tuple[str, bool]:
    """Call the LLM provider.

    Replace this body with your provider's SDK call. It's isolated here on
    purpose so the rest of the service stays provider-agnostic.

    With no API key set, returns a deterministic stub so the service runs and
    passes its probes locally without any external dependency.
    """
    if not LLM_API_KEY:
        return (f"[stub] would send to {MODEL}: {prompt[:120]}", True)

    # --- Example wiring (uncomment and add the SDK to requirements.txt) ---
    # from anthropic import Anthropic
    # client = Anthropic(api_key=LLM_API_KEY)
    # msg = client.messages.create(
    #     model=MODEL, max_tokens=max_tokens,
    #     messages=[{"role": "user", "content": prompt}],
    # )
    # return (msg.content[0].text, False)

    return (f"[configured] {MODEL} response for: {prompt[:120]}", False)
