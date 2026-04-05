"""
ChatAgent 的 HTTP 封装：多会话、OpenAPI 文档见 /docs。
"""
from __future__ import annotations

import os
import threading
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import ChatAgent

app = FastAPI(title="MyAgent API", version="1.0.0")

_cors = os.getenv("CORS_ORIGINS", "*")
_origins = [o.strip() for o in _cors.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins if _origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: dict[str, ChatAgent] = {}
_lock = threading.Lock()


def _get_or_create_agent(session_id: str) -> ChatAgent:
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = ChatAgent()
        return _sessions[session_id]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户输入")
    session_id: str | None = Field(
        None,
        description="不传则新建会话；多轮对话需带上上次返回的 session_id",
    )


class ChatResponse(BaseModel):
    reply: str
    session_id: str


class ResetRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    sid = req.session_id or str(uuid4())
    agent = _get_or_create_agent(sid)
    try:
        reply = agent.reply(req.message)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return ChatResponse(reply=reply, session_id=sid)


@app.post("/v1/chat/reset")
def reset_chat(req: ResetRequest) -> dict[str, str]:
    with _lock:
        if req.session_id not in _sessions:
            raise HTTPException(status_code=404, detail="unknown session_id")
        _sessions[req.session_id].reset()
    return {"status": "ok", "session_id": req.session_id}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=True)
