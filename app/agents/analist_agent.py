from google.adk.agents import Agent
#from rag.taco_vector_store import load_taco_vector_store --> exemplo de importação da função RAG

#taco_collection = load_taco_vector_store() quando ouver a tabela taco vetorizada

analysis_agent = Agent(
    model="google/unsloth/medgemma-4b-it:Q4_K_M",
    name="nutritional_analysis_agent",
    description="Analisa a composição nutricional de refeições e dietas.",
    instruction="""
        Você é um nutricionista analítico.
        Analise dietas e refeições, destacando:
        - calorias totais estimadas
        - proporção de macronutrientes (carboidrato, proteína, gordura)
        - adequação aos objetivos (manutenção, perda ou ganho de peso)
        - adequação as comorbidades presentes na ficha do usuário (diabetes, hipertensão, colesterol alto, sobrepeso)
        - sugestões de equilíbrio
    """,
    tools=[],
)
