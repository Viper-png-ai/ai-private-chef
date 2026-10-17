from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from hello_world.app.agents.personal_chief import (
    clear_history,
    get_history,
    list_sessions,
    stream_agent_reply,
)
from hello_world.app.models.schemas import (
    ChatRequest,
    HistoryResponse,
    SessionListResponse,
    SuccessResponse,
)
from fastapi import Depends
from hello_world.app.api.dependencies import get_current_user


router = APIRouter(prefix="/chat",tags=["chat"])

def _sse(data: dict[str, object]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

@router.get("/sessions", response_model=SessionListResponse)
def chat_sessions(
    limit: int = 50,
    user: dict[str, str] = Depends(get_current_user),
) -> SessionListResponse:
    return SessionListResponse(
        sessions=list_sessions(user["id"], limit),
    )

@router.get("/ping")
def ping()->dict[str,str]:
    return {"message": "pong"}


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    user: dict[str, str] = Depends(get_current_user),
) -> StreamingResponse:
    scoped_session_id = f"{user['id']}:{payload.session_id}"

    def event_stream() -> Iterator[str]:
        try:
            for text in stream_agent_reply(
                message=payload.message,
                user_id=user["id"],
                session_id=scoped_session_id,
                image_url=payload.image_url,
            ):
                yield _sse(
                    {
                        "type": "delta",
                        "content": text,
                    }
                )

            yield _sse({"type": "done"})
        except Exception as exc:
            yield _sse(
                {
                    "type": "error",
                    "message": str(exc),
                }
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/history",response_model=HistoryResponse)
def chat_history(
    session_id: str,
    user: dict[str, str] = Depends(get_current_user),
) ->HistoryResponse:
    if not session_id.strip():
        raise HTTPException(status_code=400,detail="session_id不能为空。")

    scoped_session_id = f"{user['id']}:{session_id}"
    
    return HistoryResponse(
        messages=get_history(scoped_session_id),
    )

@router.delete("/history/{session_id}",response_model=SuccessResponse)
def delete_chat_history(
    session_id: str,
    user: dict[str, str] = Depends(get_current_user),
)->SuccessResponse:
    if not session_id.strip():
        raise HTTPException(status_code=400,detail="session_id不能为空。")

    scoped_session_id = f"{user['id']}:{session_id}"
    clear_history(scoped_session_id)

    return SuccessResponse(success=True)
