from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from ai.models.model_connection import GeminiClient
import chromadb
from sentence_transformers import SentenceTransformer
import logging
import asyncio
import uuid
from contextlib import asynccontextmanager

# ---- Configuração de logging ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

# ---- Conexão com ChromaDB ----
def connect_chroma(path: str = "docs/my_db"):
    client = chromadb.PersistentClient(path=path)
    foods_collection = client.get_or_create_collection("foods")
    chat_collection = client.get_or_create_collection("chat_context")
    return foods_collection, chat_collection

# ---- Carregamento do modelo de embeddings ----
def load_embedder(model_name: str = "all-MiniLM-L6-v2"):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Usando device: {device}")
    return SentenceTransformer(model_name, device=device)

# ---- Consulta no banco vetorial ----
def query_db(question: str, collection, embedder, n_results: int = 5):
    query_embed = embedder.encode([question], convert_to_numpy=True)
    result = collection.query(query_embeddings=query_embed.tolist(), n_results=n_results)
    docs = result["documents"][0] if result["documents"] else []
    return "\n".join(docs) if docs else "Nenhuma informação encontrada no banco."

# ---- Consulta ao histórico do chat ----
def get_chat_context(chat_collection, embedder, user_query: str, n_results: int = 3):
    query_embed = embedder.encode([user_query], convert_to_numpy=True)
    result = chat_collection.query(query_embeddings=query_embed.tolist(), n_results=n_results)
    context_docs = result["documents"][0] if result["documents"] else []
    return "\n".join(context_docs)

# ---- Limpeza da resposta ----
def clean_response_markdown(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    clean_lines = []
    for line in lines:
        if line == "" and (len(clean_lines) == 0 or clean_lines[-1] == ""):
            continue
        clean_lines.append(line)
    return "\n".join(clean_lines)

# ---- Construção do prompt ----
def build_prompt(user_prompt: str, db_context: str, chat_context: str) -> str:
    return f"""
Você é um assistente nutricional avançado, especializado em gerar **dietas personalizadas** e fornecer informações precisas sobre alimentos.

Use apenas os dados do banco de dados 'my_db', collection 'foods'.
Não gere código e não invente valores ou alimentos.
Não repita valores e alimentos.
Se não houver dados suficientes, responda: "Informação não disponível".
Responda apenas à pergunta que o usuário fizer.
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
Use markdown com listas, **negrito** e *itálico*
Para cada alimento inclua:
Nome
Nutrientes principais
Observações sobre adequação ao critério ou comorbidade, se houver

Histórico recente da conversa:
{chat_context if chat_context else "Sem histórico prévio."}

Dados do banco:
{db_context}

Pergunta do usuário: {user_prompt}

Responda apenas como texto estruturado em Markdown.
Finalize com "Espero ter ajudado!".
"""

# ---- Estrutura do Request ----
class ChatRequest(BaseModel):
    prompt: str


# ---- Variáveis globais ----
client: GeminiClient | None = None
foods_collection = None
chat_collection = None
embedder = None


# ---- Lifespan: inicialização e finalização ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, foods_collection, chat_collection, embedder

    # Inicialização (startup)
    logger.info("Iniciando Gemini Nutrition API...")

    # Carrega banco vetorial e embeddings
    foods_collection, chat_collection = connect_chroma()
    embedder = load_embedder()

    # Carrega o modelo principal
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: GeminiClient())
    client = GeminiClient(n_ctx=2048)
    logger.info("Gemini loaded successfully")

    yield  # app roda aqui

    # Finalização (shutdown)
    logger.info("Encerrando aplicação...")

# ---- Inicialização do app ----
app = FastAPI(title="Gemini Nutrition API", lifespan=lifespan)


# ---- Endpoint raiz ----
@app.get("/")
def read_root():
    return {"message": "Gemini Nutrition API online!"}


# ---- Endpoint principal do chat ----
@app.post("/chat")
async def chat(req: ChatRequest):
    global client, foods_collection, chat_collection, embedder

    if client is None:
        raise HTTPException(status_code=503, detail="Modelo ainda carregando, tente novamente em alguns segundos.")

    user_prompt = req.prompt.strip()

    
    chat_context = get_chat_context(chat_collection, embedder, user_prompt)
    db_context = query_db(user_prompt, foods_collection, embedder)

    
    prompt = build_prompt(user_prompt, db_context, chat_context)

    response = await asyncio.get_event_loop().run_in_executor(None, lambda: client.generate(prompt))
    response = clean_response_markdown(response)

    chat_collection.add(
        documents=[f"Usuário: {user_prompt}\nAssistente: {response}"],
        metadatas=[{"type": "chat_message"}],
        ids=[f"chat_{uuid.uuid4()}"]
    )

    return {
        "prompt": user_prompt,
        "response": response.replace("```markdown\n", "")
    }
