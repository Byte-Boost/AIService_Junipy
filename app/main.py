import asyncio
import uvicorn
import os
import uuid
import time
import logging
from fastapi import FastAPI, HTTPException
from app.agents.root_agent import root_runner
from google.genai import types
from app.agents.context_agent import build_context_from_messages
from app.models.models import ChatRequest, IndevChatRequest, UserHistory, UserInfo

logger = logging.getLogger("uvicorn.error")


def create_app() -> FastAPI:
    app = FastAPI(title="Junipy AI Service")
    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Junipy API")

async def ensure_session(root_runner, user_id: str, session_id: str, app_name: str = None, retries: int = 5, delay: float = 0.2):
    """Ensure a session exists and is ready before running anything."""
    for attempt in range(retries):
        try:
            if app_name:
                await root_runner.session_service.get_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id
                )
            else:
                await root_runner.session_service.get_session(
                    user_id=user_id,
                    session_id=session_id
                )
            return
        except ValueError:
            if attempt == 0:
                if app_name:
                    await root_runner.session_service.create_session(
                        app_name=app_name,
                        user_id=user_id,
                        session_id=session_id
                    )
                else:
                    await root_runner.session_service.create_session(
                        user_id=user_id,
                        session_id=session_id
                    )
            await asyncio.sleep(delay)
    raise RuntimeError(f"Session {session_id} not found after {retries} retries")


@app.get("/")
def read_root():    
    return {"message": "Junipy API online"}

@app.post('/indevchat')
async def test_chat(req: IndevChatRequest):
    user_prompt = req.prompt
    user_id = str(uuid.uuid4())
    session_id =  f"session_{int(time.time())}_{uuid.uuid4().hex}"
    await root_runner.session_service.create_session(
            app_name="agents",
            user_id=user_id,
            session_id=session_id
        )
    user_content = types.Content(role="user", parts=[types.Part(text=user_prompt)])

    async for event in root_runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
        final_response_content = "Não consegui responder sua questão sinto muito, tente novamente."
        if event.is_final_response() and event.content and event.content.parts:
            final_response_content = event.content.parts[0].text

    return {
        "prompt": user_prompt,
        "response": final_response_content,
    }
@app.post("/chat")
async def chat(req: ChatRequest):
    logger.info(f"Received chat request: {req}")
    user_prompt = req.prompt
    user_id = str(uuid.uuid4())
    session_id = req.chatID or f"session_{int(time.time())}_{uuid.uuid4().hex}"
    if(req.userHistory is None):
        req.userHistory = UserHistory([])
    if req.userInfo is None:
        req.userInfo = UserInfo(
            id="",
            userId="",
            birthDate="",
            sex="",
            occupation="",
            consultationReason="",
            healthConditions=[],
            allergies=[],
            surgeries=[],
            activityType="",
            activityFrequency="",
            activityDuration="",
            sleepQuality="",
            wakeDuringNight="",
            bowelFrequency="",
            stressLevel="",
            alcoholConsumption="",
            smoking="",
            hydrationLevel="",
            takesMedication="",
            medicationDetails=""
        )
    context = build_context_from_messages(req.userHistory, req.userInfo)
    # enriched = enrich_context_with_analysis(context, tool_name="local_analysis")
    # thing isn't working right now
    # logger.info(f"Context for user {user_id}: {enriched}")

    try:
        if(req.chatID):
          await root_runner.session_service.get_session(
                app_name="agents",
                user_id=user_id,
                session_id=session_id
        )
        else :
            await root_runner.session_service.create_session(
            app_name="agents",
            user_id=user_id,
            session_id=session_id
        )
        # if(enriched.get("analysis")):
        #     user_prompt = f"{enriched['analysis'].get('note','')}\n\nContexto adicional:\n{enriched.get('additional_context','')}\n\n{user_prompt}"
        
        context_summary = context.get("summary", "Nenhum resumo disponível.")
        profile_summary = context.get("prompt_patch", "Nenhum perfil disponível.")
        prompt_patch = context.get("prompt_patch", "")
        user_prompt = f"Resumo do contexto:\n{context_summary}\n\n{profile_summary}\n\n{user_prompt} \n\n {prompt_patch}"

        
        user_content = types.Content(role="user", parts=[types.Part(text=user_prompt)])
        logger.debug(f"Sending prompt to agent: {user_prompt}")

        async for event in root_runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
            final_response_content = "Não consegui responder sua questão sinto muito, tente novamente."
            if event.is_final_response() and event.content and event.content.parts:
                final_response_content = event.content.parts[0].text

        return {
            "prompt": user_prompt,
            "response": final_response_content,
            "chatId": session_id,
        }
    except Exception as e:
        logger.error(f"Error processing {user_prompt}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
