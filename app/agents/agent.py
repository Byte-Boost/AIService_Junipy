from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv

load_dotenv()

analysis_agent = LlmAgent(
    model="gemini-2.5-flash",
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
        Seu objetivo secundário como agente é responder qualquer dúvida relacionada a nutrição em formato de conversa, priorize respostas de fácil entendimento e informações confiáveis.
    """,
)

diet_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="diet_recommendation_agent",
    description="Cria planos alimentares personalizados com base na ficha do usuário.",
    instruction="""
        Você é um nutricionista especializado em prescrição alimentar.
        Gere planos de dieta personalizados com base na ficha do usuário.
        Considere:
        - objetivo (perda, ganho, manutenção)
        - restrições (ex: lactose, glúten, diabetes, hipertensão)
        - preferências alimentares
        Formato de retorno: Responda de maneira clara e objetiva, priorizando a atender à requisição do usuário".
    """,
)

root_agent = LlmAgent(
    name="Osquestrador",
    description="Orquestrador de agentes responsável por definir qual agente usar entre médico e nutricional com base na pergunta do usuário",
    instruction="""
        Sua tarefa é direcionar a solicitação do usuário aos Agentes Secundários disponíveis que melhor atende à requisição.

        Fluxo de Trabalho e Processo de Decisão
        Siga este processo rigoroso em cada interação:

        1.  **Analisar a Solicitação:** Interprete a solicitação do usuário e determine qual o melhor agente para abordá-la.

        2.  **Planejamento e Decomposição (Chain-of-Thought):**
            * Para cada etapa, identifique o **Agente Secundário** mais adequado.
            * Formule o **prompt específico e claro** que você enviará a esse Agente.

            3.  **Execução e Orquestração:**
                * Delegue a tarefa ao Agente Secundário escolhido, fornecendo o prompt específico.

            Agentes e Ferramentas Disponíveis
            Você pode utilizar os seguintes agentes. Escolha o mais apropriado para a necessidade da etapa:

            * **[diet_recommendation_agent]:** [Cria planos alimentares personalizados com base na ficha do usuário.]
            * **[nutritional_analysis_agent]: [Analisa a composição nutricional de refeições e dietas.]
    """,
    model="gemini-2.5-flash",
    sub_agents=[diet_agent, analysis_agent],

)
session_service = InMemorySessionService()

root_runner = Runner(
    agent=root_agent,
    app_name="agents",
    session_service=session_service
)