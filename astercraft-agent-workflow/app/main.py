from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.domain.schemas import ChatRequest, ChatResponse, OutboxTask, RequirementState, StatsSummary
from app.services.analytics_service import AnalyticsService
from app.services.brain_service import BrainService
from app.services.outbox_service import OutboxService
from app.storage.sqlite_store import SQLiteStore

settings = get_settings()
store = SQLiteStore()
brain = BrainService(store)
outbox = OutboxService(store)
analytics = AnalyticsService(store)

app = FastAPI(
    title=settings.app_name,
    description="AI Agent workflow for enterprise gift customization.",
    version="0.1.0",
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.image_dir_path.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(settings.image_dir_path)), name="images")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "status": "ok",
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }


@app.get(f"{settings.api_v1_prefix}/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


@app.post(f"{settings.api_v1_prefix}/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return await brain.handle_chat(request)


@app.get(f"{settings.api_v1_prefix}/sessions/{{user_id}}", response_model=RequirementState)
async def get_session(user_id: str):
    state = store.get_session_state(user_id)
    if not state:
        raise HTTPException(status_code=404, detail="session not found")
    return RequirementState(**state)


@app.get(f"{settings.api_v1_prefix}/outbox/pending", response_model=list[OutboxTask])
async def pending_outbox(limit: int = Query(default=20, ge=1, le=100)):
    return outbox.pending(limit=limit)


@app.post(f"{settings.api_v1_prefix}/outbox/ack/{{task_id}}")
async def ack_outbox(task_id: str):
    ok = outbox.ack(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="pending task not found")
    return {"status": "acked", "task_id": task_id}


@app.get(f"{settings.api_v1_prefix}/stats/summary", response_model=StatsSummary)
async def stats_summary():
    return analytics.summary()
