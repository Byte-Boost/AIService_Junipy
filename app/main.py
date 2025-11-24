from app.models.models import ChatRequest, IndevChatRequest, UserHistory, UserInfo
from app.agents.context_agent import build_context_from_messages
from app.agents.anamnesis_agent import anamnesis_runner
from fastapi import FastAPI, HTTPException, Header
from app.agents.root_agent import root_runner
from jwt.exceptions import InvalidTokenError
from app.context import jwt_token_ctx
from dotenv import load_dotenv
from google.genai import types
import requests
import uvicorn
import logging
import json
import uuid
import time
import jwt
import os

logger = logging.getLogger("uvicorn.error")

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL")


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
    try:
        # Decodifica o token sem verificar a assinatura (ajuste conforme necessário)
        payload = jwt.decode(token, options={"verify_signature": False})
        # Tenta diferentes campos comuns em JWTs
        user_id = (
            payload.get("sub")
            or payload.get("user_id")
            or payload.get("id")
            or payload.get("userId")
        )
        if user_id:
            return str(user_id)
        return "user_default"
    except InvalidTokenError as e:
        logger.warning(f"Erro ao decodificar token JWT: {e}")
        return "user_default"


def verify_anamnesis():
    token = jwt_token_ctx.get()

    if not token:
        return "Erro: Token de autenticação não encontrado. Certifique-se de enviar o header Authorization."
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    response = requests.get(API_BASE_URL + "/user/profile-data", headers=headers)

    print("Status code da verificação de anamnese: ", response.status_code)

    print("Resposta da verificação de anamnese: ", response.json())

    return response.json()


# async def ensure_session(root_runner, user_id: str, session_id: str, app_name: str = None, state: dict = None, retries: int = 5, delay: float = 0.2):
#     """Ensure a session exists and is ready before running anything."""
#     for attempt in range(retries):
#         try:
#             if app_name:
#                 session = await root_runner.session_service.get_session(
#                     app_name=app_name,
#                     user_id=user_id,
#                     session_id=session_id
#                 )
#             else:
#                 session = await root_runner.session_service.get_session(
#                     user_id=user_id,
#                     session_id=session_id
#                 )

#             # Se chegou aqui, a sessão existe
#             if session:
#                 return session

#         except (ValueError, Exception) as e:
#             if attempt == 0:
#                 # Primeira tentativa de criar a sessão
#                 try:
#                     if app_name:
#                         if state:
#                             await root_runner.session_service.create_session(
#                                 app_name=app_name,
#                                 user_id=user_id,
#                                 session_id=session_id,
#                                 state=state
#                             )
#                         else:
#                             await root_runner.session_service.create_session(
#                                 app_name=app_name,
#                                 user_id=user_id,
#                                 session_id=session_id
#                             )
#                     else:
#                         if state:
#                             await root_runner.session_service.create_session(
#                                 user_id=user_id,
#                                 session_id=session_id,
#                                 state=state
#                             )
#                         else:
#                             await root_runner.session_service.create_session(
#                                 user_id=user_id,
#                                 session_id=session_id
#                             )
#                 except Exception as create_error:
#                     logger.warning(f"Erro ao criar sessão (tentativa {attempt+1}): {create_error}")

#             await asyncio.sleep(delay)

#     raise RuntimeError(f"Session {session_id} not found after {retries} retries")


@app.get("/")
def read_root():
    return {"message": "Junipy API online"}


@app.post("/indevchat")
async def test_chat(
    req: IndevChatRequest, authorization: str = Header(None, description="Bearer token")
):
    """
    Endpoint para realizar anamnese completa.
    Mantém o estado da sessão entre requisições para o mesmo usuário.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid authorization format. Use 'Bearer <token>'"
        )

    token = authorization.replace("Bearer ", "")
    jwt_token_ctx.set(token)

    user_prompt = req.prompt
    user_id = get_user_id_from_token(token)
    session_id = f"anamnesis_{user_id}"

    data = verify_anamnesis()
    print("----------------------")
    print(data)
    print("----------------------")

    fields_to_check = {k: v for k, v in data.items() if k != "id"}

    needs_anamnesis = any(
        v == "string" or v == "" or v is None or v == []
        for v in fields_to_check.values()
    )

    if needs_anamnesis:
        logger.info(
            f"Usuario {user_id} iniciando/continuando anamnese (sessão: {session_id})"
        )

        initial_state = {
            "name": "",
            "birthDate": "",
            "sex": "",
            "weight": "",
            "height": "",
            "occupation": "",
            "consultationReason": "",
            "healthConditions": [],
            "allergies": [],
            "surgeries": [],
            "activityType": "",
            "activityFrequency": "",
            "activityDuration": "",
            "sleepQuality": "",
            "wakeDuringNight": "",
            "bowelFrequency": "",
            "stressLevel": "",
            "alcoholConsumption": "",
            "smoking": "",
            "hydrationLevel": "",
            "takesMedication": "",
            "medicationDetails": ""
        }

        session_exists = False
        try:
            session = await anamnesis_runner.session_service.get_session(
                app_name="agents", user_id=user_id, session_id=session_id
            )
            if session:
                session_exists = True
                logger.info(
                    f"Sessão existente encontrada com state: {dict(session.state) if hasattr(session, 'state') else 'sem state'}"
                )
        except Exception as e:
            logger.info(f"Sessão não encontrada: {e}")

        if not session_exists:
            try:
                logger.info("Criando nova sessão de anamnese...")
                await anamnesis_runner.session_service.create_session(
                    app_name="agents",
                    user_id=user_id,
                    session_id=session_id,
                    state=initial_state,
                )
                logger.info("Nova sessão criada com sucesso")
            except Exception as create_error:
                logger.error(f"Erro ao criar sessão: {create_error}")
                raise HTTPException(
                    status_code=500, detail=f"Erro ao criar sessão: {str(create_error)}"
                )

        user_content = types.Content(role="user", parts=[types.Part(text=user_prompt)])
        final_response_content = (
            "Não consegui responder sua questão sinto muito, tente novamente."
        )

        try:
            async for event in anamnesis_runner.run_async(
                user_id=user_id, session_id=session_id, new_message=user_content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response_content = event.content.parts[0].text
        except Exception as e:
            logger.error(f"Erro durante run_async: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")

        return {
            "prompt": user_prompt,
            "response": final_response_content,
            "session_id": session_id,
            "user_id": user_id,
        }

    # CHAT NORMAL COM ORQUESTRADOR
    else:
        pass
        # logger.info(f"Received chat request: {req}")
        # user_prompt = req.prompt
        # user_id = str(uuid.uuid4())
        # session_id = req.chatID or f"session_{int(time.time())}_{uuid.uuid4().hex}"
        # if(req.userHistory is None):
        #     req.userHistory = UserHistory([])

        # context = build_context_from_messages(req.userHistory, req.userInfo)

        # try:
        #     if(req.chatID):
        #         await root_runner.session_service.get_session(
        #             app_name="agents",
        #             user_id=user_id,
        #             session_id=session_id
        #         )
        #     else:
        #         await root_runner.session_service.create_session(
        #             app_name="agents",
        #             user_id=user_id,
        #             session_id=session_id
        #         )

        #     await root_runner.session_service.create_session(
        #         app_name="agents",
        #         user_id=user_id,
        #         session_id=session_id
        #     )

        #     user_content = types.Content(role="user", parts=[types.Part(text=user_prompt)])
        #     logger.debug(f"Sending prompt to agent: {user_prompt}")

        #     async for event in root_runner.run_async(
        #         user_id=user_id, session_id=session_id, new_message=user_content
        #     ):
        #         final_response_content = "Não consegui responder sua questão sinto muito, tente novamente."
        #         if event.is_final_response() and event.content and event.content.parts:
        #             final_response_content = event.content.parts[0].text

        #     return {
        #         "prompt": user_prompt,
        #         "response": final_response_content,
        #         "chatId": session_id,
        #     }
        # except Exception as e:
        #     logger.error(f"Error processing {user_prompt}: {e}")
