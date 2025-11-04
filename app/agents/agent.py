from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from diet_agent import diet_agent
from analysis_agent import analysis_agent
from dotenv import load_dotenv

load_dotenv()

root_agent = LlmAgent(
    name="Orquestrador",
    description="Orquestrador de agentes responsável por definir qual agente usar entre médico e nutricional com base na pergunta do usuário",
    instruction="""
        Caso receba uma informação em outra linguagem que não seja português tente utilizar o tradutor interno para responder isso também inclui termos técnicos.
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
     include_contents="default",
    sub_agents=[diet_agent, analysis_agent],
)

session_service = InMemorySessionService()

root_runner = Runner(
    agent=root_agent,
    app_name="agents",
    session_service=session_service
)
