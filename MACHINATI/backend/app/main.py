import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from . import config
from .db import init_db
from .routes.machines import router as machines_router
from .routes.requests import router as requests_router
from .whatsapp import verify_signature
from .service import handle_message

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("machinati")

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title="MACHINATI API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["GET","POST","PATCH"], allow_headers=["*"])
app.include_router(requests_router)
app.include_router(machines_router)

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/webhook/whatsapp")
def verify_webhook(request: Request):
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and config.VERIFY_TOKEN and p.get("hub.verify_token") == config.VERIFY_TOKEN:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(p.get("hub.challenge", ""))
    raise HTTPException(403, "Invalid verification token")

async def process_messages(messages):
    for message in messages:
        try: await handle_message(message)
        except Exception: log.exception("Failed to process WhatsApp message")

@app.post("/webhook/whatsapp")
async def receive_webhook(request: Request, tasks: BackgroundTasks):
    body = await request.body()
    if not verify_signature(body, request.headers.get("x-hub-signature-256")):
        raise HTTPException(403, "Invalid webhook signature")
    try: payload = json.loads(body)
    except ValueError: raise HTTPException(400, "Invalid JSON")
    messages = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            messages.extend(change.get("value", {}).get("messages", []))
    if messages: tasks.add_task(process_messages, messages)
    return {"received":True}
