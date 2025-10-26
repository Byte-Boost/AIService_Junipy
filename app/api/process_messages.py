from typing import List, Dict, Any, Optional
import os
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.agents.context_agent import build_context_from_messages
from app.agents.text_analysis import enrich_context_with_analysis
from app.database import get_database_client

router = APIRouter(prefix="/api/v1")

logger = logging.getLogger("uvicorn.error")


class ChatMessage(BaseModel):
    role: str
    message: str
    chatId: Optional[str] = None
    createdAt: Optional[str] = None


class MessagesPayload(BaseModel):
    userId: str
    messages: List[ChatMessage]


@router.post("/processMessages")
async def process_messages(payload: MessagesPayload, summary_only: bool = Query(True, description="If true, return only the context summary")) -> Dict[str, Any]:
    try:
        messages = [m.dict() for m in payload.messages]
        db_client = None
        profile = None
        try:
            db_client = get_database_client()
            profile = db_client.get_user_profile(payload.userId)
        except Exception:
            profile = None

        context = build_context_from_messages(messages, profile=profile)

        prompt_patch = context.get("prompt_patch")
        if prompt_patch:
            logger.info("Updated prompt for user %s:\n%s", payload.userId, prompt_patch)
            print(f"[prompt_patch] user={payload.userId}\n{prompt_patch}\n")

        enriched = enrich_context_with_analysis(context, tool_name="local_analysis")

        if db_client and hasattr(db_client, "close"):
            try:
                db_client.close()
            except Exception:
                pass

        if summary_only:
            return {"summary": context.get("summary")}

        return {"userId": payload.userId, "messageCount": len(messages), "context": enriched}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing messages: {str(e)}")
