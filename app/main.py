import uvicorn
import os
import uuid
import time
import logging
from fastapi import FastAPI, HTTPException
from app.agents.agent import root_runner
from google.genai import types
from pydantic import BaseModel
import logging



logger = logging.getLogger("uvicorn.error")


def create_app() -> FastAPI:
    app = FastAPI(title="Junipy AI Service")
    # app.include_router(process_router)
    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Junipy API")

class ChatRequest(BaseModel):
    prompt: str

@app.get("/")
def read_root():
    return {"message": "Junipy API online"}

@app.post("/chat")
async def chat(req: ChatRequest):

    user_prompt = req.prompt
    user_id = str(uuid.uuid4())
    session_id = f"session_{int(time.time())}"
    try:
        await root_runner.session_service.create_session(
            app_name="agents",
            user_id=user_id,
            session_id=session_id
        )
        user_content = types.Content(role="user", parts=[types.Part(text=user_prompt)])
        final_response_content = "No response received."
        async for event in root_runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
            if event.is_final_response() and event.content and event.content.parts:
                final_response_content = event.content.parts[0].text
        return {
            "prompt": user_prompt,
            "response": final_response_content
        }
    except Exception as e:
        logger.error(f"Error processing {user_prompt}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
