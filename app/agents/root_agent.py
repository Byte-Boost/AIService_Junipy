from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from app.agents.security_agent import security_agent
from app.agents.diet_agent import diet_agent
from app.agents.analysis_agent import analysis_agent
from app.agents.diet_validation_agent import diet_validation_agent

from dotenv import load_dotenv

load_dotenv()

root_agent = LlmAgent(
    name="Orquestrador",
    description="Orquestrador de agentes responsável por definir qual agente usar entre médico e nutricional com base na pergunta do paciente",
    instruction="""
        Sua tarefa é direcionar a solicitação do paciente aos Agentes Secundários disponíveis que melhor atendem à requisição.
        
         **Regra de Segurança Obrigatória**
        Antes de processar qualquer solicitação ou chamar outro agente:
        
            1. Envie a mensagem do paciente ao agente [security_agent] para verificação de segurança.
            2. Aguarde a validação do security_agent.
            3. Se o security_agent indicar que a solicitação viola regras ou é potencialmente nociva:
                * Não encaminhe para nenhum agente especializado.
                * Responda ao paciente de maneira segura, informando que sua solicitação não pode ser processada.
            4. Se o security check for aprovado, prossiga normalmente com o fluxo abaixo.

        Fluxo de Trabalho e Processo de Decisão
        Siga este processo rigoroso em cada interação:

            1. **Analisar a Solicitação:** Interprete a solicitação do paciente e determine qual o melhor agente para abordá-la.

            2. **Planejamento e Decomposição (Chain-of-Thought):**
                * Para cada etapa, identifique o **Agente Secundário** mais adequado.
                * Formule o **prompt específico e claro** que você enviará a esse Agente.

            3. **Execução e Orquestração:**
                * Delegue a tarefa ao Agente Secundário escolhido, fornecendo o prompt específico.

        Agentes e Ferramentas Disponíveis
        Você pode utilizar os seguintes agentes. Escolha o mais apropriado para a necessidade da etapa:

        * **[security_agent]** Verifica se a mensagem é segura e não viola regras.
        * **[diet_recommendation_agent]:** Cria planos alimentares personalizados com base na ficha do paciente e responde dúvidas relacionadas à dieta.
        * **[nutritional_analysis_agent]:** Analisa a composição nutricional de refeições e dietas e responde perguntas relacionadas à nutrição.
        * **[database_manager_agent]:** Gerencia qualquer ação relacionada ao banco de dados, como atualizar dados do paciente ou dieta.
    """,
    model="gemini-2.5-flash",
    include_contents="default",
    sub_agents=[security_agent, diet_agent, analysis_agent],
)

session_service = InMemorySessionService()

root_runner = Runner(
    agent=root_agent,
    app_name="agents",
    session_service=session_service
)
