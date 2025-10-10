from google.adk.agents import Agent
#from rag.taco_vector_store import load_taco_vector_store --> exemplo de importação da função RAG

#taco_collection = load_taco_vector_store() quando ouver a tabela taco vetorizada

def taco_search_tool(query: str):
    """Busca alimentos adequados para recomendações."""
    results = taco_collection.query(query_texts=[query], n_results=5)
    docs = results["documents"][0]
    return {"foods": docs}

diet_recommendation_agent = Agent(
    model="google/unsloth/medgemma-4b-it:Q4_K_M",
    name="diet_recommendation_agent",
    description="Cria planos alimentares personalizados com base na ficha do usuário.",
    instruction="""
        Você é um nutricionista especializado em prescrição alimentar.
        Gere planos de dieta personalizados com base na ficha do usuário.
        Considere:
        - objetivo (perda, ganho, manutenção)
        - restrições (ex: lactose, glúten, diabetes, hipertensão)
        - preferências alimentares
        - uso da Tabela TACO como base nutricional
        Sempre use a ferramenta taco_search_tool para sugerir alimentos com base científica.
    """, 
    tools=[], #tools=[taco_search_tool] quando ouver.
)
