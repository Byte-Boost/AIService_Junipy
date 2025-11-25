from fastapi import FastAPI, HTTPException, Header
from app.agents.root_agent import root_runner
from google.genai import types
from app.models.models import ChatRequest, IndevChatRequest, UserHistory, UserInfo
from app.context import jwt_token_ctx
import uvicorn
import os
import logging
import jwt
from jwt import ExpiredSignatureError, DecodeError
import asyncio

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


def get_user_id_from_token(token: str) -> str:
    """Extrai o user_id do token JWT"""
    print(token)
    try:
        # Decodifica o token sem verificar a assinatura (ajuste conforme necessário)
        payload = jwt.decode(token, options={"verify_signature": False})
        # Tenta diferentes campos comuns em JWTs
        print(payload)
        user_id = (
            payload.get("userId")
            or payload.get("sub")
            or payload.get("user_id")
            or payload.get("id")
            or payload.get("userID")
        )
        if user_id:
            return str(user_id)
        return "user_default"
    except (ExpiredSignatureError, DecodeError) as e:
        logger.warning(f"Erro ao decodificar token JWT: {e}")
        return "user_default"


async def ensure_session(root_runner, user_id: str, session_id: str, app_name: str = None, state: dict = None, retries: int = 5, delay: float = 0.2):
    for attempt in range(retries):
        try:
            # Log the session fetch attempt
            logger.info(f"Attempt {attempt+1}: Checking if session {session_id} exists for user {user_id}")

            if app_name:
                session = await root_runner.session_service.get_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id
                )

            if session:
                logger.info(f"Session {session_id} found for user {user_id}")
                return session
            else:
                logger.warning(f"Session {session_id} not found for user {user_id}")
                session = await root_runner.session_service.create_session(
                    app_name=app_name or "agents",
                    user_id=user_id,
                    session_id=session_id,
                )
                return session
            

        except Exception as e:
            logger.warning(f"Error during session check (attempt {attempt+1}): {e}")

        await asyncio.sleep(delay)

    logger.error(f"Session {session_id} not found after {retries} retries")
    raise RuntimeError(f"Session {session_id} not found after {retries} retries")


@app.get("/")
def read_root():
    return {"message": "Junipy API online"}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest, authorization: str = Header(None, description="Bearer token")):
    """
    Endpoint para chat geral com roteamento entre agentes.
    Mantém o estado da sessão entre requisições para o mesmo usuário.
    """
    # 1. Verificar a autorização
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid authorization format. Use 'Bearer <token>'"
        )

    print(authorization)
    token = authorization.replace("Bearer ", "")
    print(token)
    jwt_token_ctx.set(token)  # Definir o token no contexto

    user_prompt = req.prompt
    user_id = get_user_id_from_token(token)
    session_id = req.chatID

    # 2. Logar o início/continuação do chat
    logger.info(f"Usuário {user_id} iniciando/continuando chat geral (sessão: {session_id})")

    # 3. Verificar se a sessão existe. Se não, criar uma nova.
    try:
        session = await ensure_session(
            root_runner, 
            app_name="agents", 
            user_id=user_id, 
            session_id=session_id
        )
        if not session:
            raise HTTPException(status_code=404, detail=f"Sessão {session_id} não encontrada e não foi possível criar.")
    except Exception as e:
        logger.error(f"Erro ao verificar ou criar sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar ou criar a sessão: {str(e)}")

    # 4. Preparar o conteúdo da mensagem do usuário
    user_content = types.Content(role="user", parts=[types.Part(text=user_prompt)])
    final_response_content = "Não consegui responder sua questão, sinto muito. Tente novamente."

    # 5. Tentar obter a resposta do agente
    try:
        async for event in root_runner.run_async(
            user_id=user_id, session_id=session_id, new_message=user_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_response_content = event.content.parts[0].text

    except Exception as e:
        logger.error(f"Erro ao processar a mensagem do usuário: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar sua solicitação: {str(e)}")

    # 6. Retornar a resposta final para o usuário
    return {
        "prompt": user_prompt,
        "response": final_response_content,
        "session_id": session_id,
        "user_id": user_id,
    }
