"""
Orchestrator — receives GitHub webhooks and drives the display.
Agents are self-polling; the orchestrator provides visibility.
"""
import os
import hmac
import hashlib
import logging
from fastapi import FastAPI, Request, HTTPException
from orchestrator.display import update_agent_status, get_display
from orchestrator.router import LABEL_TO_AGENT

app = FastAPI(title="Agentic Team Orchestrator")
logger = logging.getLogger(__name__)


@app.post("/webhook")
async def github_webhook(request: Request):
    """Receive GitHub webhook events and update agent display."""
    # Validate signature
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    body = await request.body()
    if secret:
        sig = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    if event == "issues":
        action = payload.get("action")
        issue_number = payload["issue"]["number"]
        labels = [label["name"] for label in payload["issue"]["labels"]]

        for label in labels:
            if label in LABEL_TO_AGENT:
                agent = LABEL_TO_AGENT[label]
                if agent is not None:
                    update_agent_status(agent, f"Issue #{issue_number} — {label}")
                    logger.info(f"Issue #{issue_number} -> {agent} ({label})")

    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/status")
async def status():
    return get_display()
