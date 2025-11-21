import asyncio
import uvicorn
import os
import uuid
import time
import logging
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import FastAPI, HTTPException, Header
from app.agents.root_agent import root_runner
from app.agents.anamnesis_agent import anamnesis_runner
from google.genai import types
from app.agents.context_agent import build_context_from_messages
from app.models.models import ChatRequest, IndevChatRequest, UserHistory, UserInfo
from app.context import jwt_token_ctx

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
    try:
        # Decodifica o token sem verificar a assinatura (ajuste conforme necessário)
        payload = jwt.decode(token, options={"verify_signature": False})
        # Tenta diferentes campos comuns em JWTs
        user_id = payload.get('sub') or payload.get('user_id') or payload.get('id') or payload.get('userId')
        if user_id:
            return str(user_id)
        return "user_default"
    except InvalidTokenError as e:
        logger.warning(f"Erro ao decodificar token JWT: {e}")
        return "user_default"


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


@app.post('/indevchat')
async def test_chat(
    req: IndevChatRequest,
    authorization: str = Header(None, description="Bearer token")
):
    """
    Endpoint para realizar anamnese completa.
    Mantém o estado da sessão entre requisições para o mesmo usuário.
    """
    # Extrair o token do header Authorization
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization format. Use 'Bearer <token>'")
    
    token = authorization.replace('Bearer ', '')
    jwt_token_ctx.set(token)
    
    user_prompt = req.prompt
    user_id = get_user_id_from_token(token)
    session_id = f"anamnesis_{user_id}"
    
    logger.info(f"Usuario {user_id} iniciando/continuando anamnese (sessão: {session_id})")
    
    # Estado inicial da anamnese
    initial_state = {
        "birthDate": "",
        "sex": "",
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
        "medicationDetails": "",
    }
    
    # Verificar se já existe uma sessão
    session_exists = False
    try:
        session = await anamnesis_runner.session_service.get_session(
            app_name="agents",
            user_id=user_id,
            session_id=session_id
        )
        if session:
            session_exists = True
            logger.info(f"Sessão existente encontrada com state: {dict(session.state) if hasattr(session, 'state') else 'sem state'}")
    except Exception as e:
        logger.info(f"Sessão não encontrada: {e}")
    
    # Se não existe, criar nova sessão com o state inicial
    if not session_exists:
        try:
            logger.info("Criando nova sessão de anamnese...")
            await anamnesis_runner.session_service.create_session(
                app_name="agents",
                user_id=user_id,
                session_id=session_id,
                state=initial_state
            )
            logger.info("Nova sessão criada com sucesso")
        except Exception as create_error:
            logger.error(f"Erro ao criar sessão: {create_error}")
            raise HTTPException(status_code=500, detail=f"Erro ao criar sessão: {str(create_error)}")
    
    user_content = types.Content(role="user", parts=[types.Part(text=user_prompt)])
    final_response_content = "Não consegui responder sua questão sinto muito, tente novamente."
    
    try:
        async for event in anamnesis_runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=user_content
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
        "user_id": user_id
    }


@app.post('/indevchat/reset')
async def reset_anamnesis_session(
    authorization: str = Header(None, description="Bearer token")
):
    """
    Reseta a sessão de anamnese do usuário, apagando todos os dados coletados.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization format. Use 'Bearer <token>'")
    
    token = authorization.replace('Bearer ', '')
    user_id = get_user_id_from_token(token)
    session_id = f"anamnesis_{user_id}"
    
    try:
        await anamnesis_runner.session_service.delete_session(
            app_name="agents",
            user_id=user_id,
            session_id=session_id
        )
        logger.info(f"Sessão de anamnese do usuário {user_id} foi resetada")
        return {"message": "Sessão de anamnese resetada com sucesso", "user_id": user_id}
    except Exception as e:
        logger.warning(f"Erro ao resetar sessão: {e}")
        return {"message": "Nenhuma sessão ativa encontrada para resetar", "user_id": user_id}


# @app.get('/indevchat/status')
# async def get_anamnesis_status(
#     authorization: str = Header(None, description="Bearer token")
# ):
#     """
#     Retorna o status atual da anamnese do usuário.
#     """
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header is required")
    
#     if not authorization.startswith('Bearer '):
#         raise HTTPException(status_code=401, detail="Invalid authorization format. Use 'Bearer <token>'")
    
#     token = authorization.replace('Bearer ', '')
#     user_id = get_user_id_from_token(token)
#     session_id = f"anamnesis_{user_id}"
    
#     try:
#         session = await root_runner.session_service.get_session(
#             app_name="agents",
#             user_id=user_id,
#             session_id=session_id
#         )
        
#         if session and hasattr(session, 'state') and session.state:
#             # Conta campos preenchidos
#             filled = sum(1 for v in session.state.values() if v not in (None, "", [], {}))
#             total = len(session.state)
            
#             return {
#                 "user_id": user_id,
#                 "session_exists": True,
#                 "filled_fields": filled,
#                 "total_fields": total,
#                 "progress_percent": round((filled / total) * 100, 2),
#                 "state": dict(session.state)
#             }
#         else:
#             return {
#                 "user_id": user_id,
#                 "session_exists": False,
#                 "message": "Nenhuma sessão de anamnese encontrada"
#             }
#     except Exception as e:
#         logger.warning(f"Erro ao buscar status: {e}")
#         return {
#             "user_id": user_id,
#             "session_exists": False,
#             "message": f"Erro: {str(e)}"
#         }


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

    try:
        if(req.chatID):
            await root_runner.session_service.get_session(
                app_name="agents",
                user_id=user_id,
                session_id=session_id
            )
        else:
            await root_runner.session_service.create_session(
                app_name="agents",
                user_id=user_id,
                session_id=session_id
            )
        
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