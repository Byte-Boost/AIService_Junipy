from fastapi import FastAPI
from pydantic import BaseModel
from .ai.models.model_connection import MedGemmaClient 
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="MedGemma Nutrition API")

def clean_response_markdown(text: str) -> str:

    lines = [line.strip() for line in text.splitlines()]
    
    clean_lines = []
    for line in lines:
        if line == "" and (len(clean_lines) == 0 or clean_lines[-1] == ""):
            continue
        clean_lines.append(line)
    

    return "\n".join(clean_lines)


class ChatRequest(BaseModel):
    prompt: str


client = MedGemmaClient()

@app.get("/")
def read_root():
    return {"message": "MedGemma Nutrition API online!"}

@app.post("/chat")
async def chat(req: ChatRequest):
    logger.info(req.model_dump_json())
    user_prompt = req.prompt
    prompt_template = f"""
    Você é um assistente de nutrição especializado em comorbidades.

    Sua tarefa:
    - Responda à pergunta do usuário de forma clara, objetiva e baseada em evidências científicas.
    - Priorize informações essenciais e relevantes para o contexto clínico.
    - Limite a resposta ao máximo de tokens permitido, sem perder o significado.
    - Não inclua introduções, despedidas ou textos fora da resposta principal.
    - Use linguagem acessível, evitando jargões técnicos complexos.
    - Utilize markdown para formatar a resposta, incluindo negrito, itálico e listas.

    Pergunta do usuário: {user_prompt}
    """

    response = client.generate(user_prompt)

    return {
        "prompt": user_prompt,
        "response": response
    }
