import os
import logging
from fastapi import FastAPI
import uvicorn

from app.api.process_messages import router as process_router

logger = logging.getLogger("uvicorn.error")


def create_app() -> FastAPI:
    app = FastAPI(title="Junipy AI Service")
    app.include_router(process_router)
    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ai.models.model_connection import MedGemmaClient
import chromadb
from sentence_transformers import SentenceTransformer
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="MedGemma Nutrition API")

def connect_chroma(path: str = "docs/my_db", collection_name: str = "foods"):
    client = chromadb.PersistentClient(path=path)
    collection = client.get_or_create_collection(collection_name)
    return collection

def load_embedder(model_name: str = "all-MiniLM-L6-v2"):
    return SentenceTransformer(model_name)

def query_db(question: str, collection, embedder, n_results: int = 5):
    query_embed = embedder.encode([question], convert_to_numpy=True)
    result = collection.query(query_embeddings=query_embed.tolist(), n_results=n_results)
    docs = result["documents"][0] if result["documents"] else []
    return "\n".join(docs) if docs else "Nenhuma informação encontrada no banco."

def clean_response_markdown(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    clean_lines = []
    for line in lines:
        if line == "" and (len(clean_lines) == 0 or clean_lines[-1] == ""):
            continue
        clean_lines.append(line)
    return "\n".join(clean_lines)

def build_prompt(user_prompt: str, db_context: str) -> str:
    return f"""
Você é um assistente nutricional avançado, especializado em gerar **dietas personalizadas** e fornecer informações precisas sobre alimentos.

Use apenas os dados do banco de dados 'my_db', collection 'foods'.
Não gere código e não invente valores ou alimentos.
Não repita valores e alimentos.
Se não houver dados suficientes, responda: "Informação não disponível".
Responda apenas a pregunta que o usuário fizer.
Não invente ou responda perguntas adicionais.
Guarde as informações do usuário.

Se o usuário mencionar comorbidades como hipertensão, diabetes, colesterol alto ou sobrepeso, siga estas restrições:
Hipertensão: evitar sódio acima de 200 mg
Diabetes: priorizar fibras e reduzir carboidratos simples
Colesterol alto: evitar colesterol acima de 50 mg e gorduras saturadas
Sobrepeso: priorizar alimentos de baixa densidade calórica

Para perguntas sobre nutrientes:
Compare os valores dos alimentos no banco
Liste apenas os alimentos que atendam ao critério solicitado (ex: ricos em proteína, baixo em carboidrato)

Formato da resposta:
Texto humano, estruturado e legível
Use markdown com listas, negrito e itálico
Para cada alimento inclua:
Nome
Nutrientes principais
Observações sobre adequação ao critério ou comorbidade, se houver

Dados do banco:
{db_context}

Pergunta do usuário: {user_prompt}

Responda apenas como texto estruturado em Markdown.
Finalize com "Espero ter ajudado!".
"""

class ChatRequest(BaseModel):
    prompt: str

client: MedGemmaClient | None = None
collection = connect_chroma()
embedder = load_embedder()

@app.on_event("startup")
async def load_model():
    global client
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: MedGemmaClient())
    client = MedGemmaClient(n_ctx=2048)
    logger.info("MedGemma loaded successfully")

@app.get("/")
def read_root():
    return {"message": "MedGemma Nutrition API online!"}

@app.post("/chat")
async def chat(req: ChatRequest):
    global client
    if client is None:
        raise HTTPException(status_code=503, detail="Modelo ainda carregando, tente novamente em alguns segundos.")

    user_prompt = req.prompt
    db_context = query_db(user_prompt, collection, embedder)
    prompt = build_prompt(user_prompt, db_context)
    response = client.generate(prompt)
    response = clean_response_markdown(response)

    return {
        "prompt": user_prompt,
        "response": response.replace("```markdown\n", "")
    }
