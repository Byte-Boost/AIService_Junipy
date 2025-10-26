from typing import List, Dict, Any, Optional
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
    userProfile: Optional[dict] = None  # 🔹 Agora o perfil vem no payload


@router.post("/processMessages")
async def process_messages(
    payload: MessagesPayload,
    summary_only: bool = Query(True, description="If true, return only the context summary")
) -> Dict[str, Any]:
    try:
        messages = [m.dict() for m in payload.messages]

        # 🔹 Conexão com o banco apenas para salvar logs ou mensagens
        db_client = get_database_client()

        # 🔹 Construir o contexto com o perfil vindo do backend Java
        context = build_context_from_messages(messages, profile=payload.userProfile)

        prompt_patch = context.get("prompt_patch")
        if prompt_patch:
            logger.info("Updated prompt for user %s:\n%s", payload.userId, prompt_patch)
            print(f"[prompt_patch] user={payload.userId}\n{prompt_patch}\n")

        # 🔹 Enriquecimento local do contexto
        enriched = enrich_context_with_analysis(context, tool_name="local_analysis")

        # 🔹 Salva resultado ou logs no Mongo (opcional)
        try:
            db_client.save_chat_messages(payload.userId, messages)
            db_client.save_context_summary(payload.userId, {"summary": context.get("summary")})
        except Exception as e:
            logger.warning(f"Erro ao salvar logs no banco: {e}")
        finally:
            db_client.close()

        # 🔹 Retorno
        if summary_only:
            return {"summary": context.get("summary")}

        return {"userId": payload.userId, "messageCount": len(messages), "context": enriched}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing messages: {str(e)}")
