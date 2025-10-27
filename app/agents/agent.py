from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv
import chromadb

load_dotenv()

client = chromadb.PersistentClient(path="../../docs/my_db")

nutrition = client.get_or_create_collection(name="nutrition")
comorbidity = client.get_or_create_collection(name="comorbidity")

def search_nutrition_tool(query: str):
    results = nutrition.query(
        query_texts=[query], 
        n_results=5,
    )
    texts = [item for sublist in results['documents'] for item in sublist]
    return "\n".join(texts)

def search_comorbidity_tool(query: str):
    results = comorbidity.query(
        query_texts=[query], 
        n_results=5,
    )
    texts = [item for sublist in results['documents'] for item in sublist]
    return "\n".join(texts)

def search_all_tool(query: str):
    results_nutrition = nutrition.query(
        query_texts=[query], 
        n_results=3,
    )

    results_comorbidity = comorbidity.query(
        query_texts=[query], 
        n_results=3,
    )

    texts_nutrition = [item for sublist in results_nutrition['documents'] for item in sublist]
    texts_comorbidity = [item for sublist in results_comorbidity['documents'] for item in sublist]

    return "\n".join(texts_nutrition + texts_comorbidity)

analysis_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="nutritional_analysis_agent",
    description="Analisa a composição nutricional de refeições e dietas.",
    instruction="""
        Contexto: Você é um agente nutricional especialista na análise de dieta e em responder dúvidas da área nutricional
        
        Conteúdo principal: Sua principal tarefa é responder dúvidas da área nutricional de maneira coesa e linguagem acessível, além de avaliar dietas nutricionais personalizadas tendo como base informações fornecidas pelo usuário como gênero, idade, peso, altura.

        Restrições: Não forneça dados sensíveis do usuário e responda as dúvidas do usuário de maneira ética com uma abordagem amigável.

        Formato de Saída: A resposta retornada para o usuário deve ser um texto curto de em média 30 palavras, mas que contenha a resposta necessária para o usuário.

        Exemplos:
            Exemplo 1:
                Dieta de Sandro
                    ...
                    ## Café da manhã
                    - Opção 1: 1 iogurte desnatado com 1 colher de aveia e 3 morangos
                    ...

                Pergunta do usuário: Não gosto de iogurte, o que posso colocar no lugar?

                Resposta: No caso de sua dieta, uma boa alternativa seria a substituição do iogurte por 1/2 xícara de café sem açúcar ou 1/2 xícara de chá.

            Exemplo 2:
                Pergunta do usuário: Qual a composição nutricional do arroz integral cozido?

                Resposta: O arroz integral cozido possui 2.6g de proteínas, 25.8g de carboidratos e 2.7g de fibras alimentares.

        Conteúdo de Suporte:
            Na necessidade de buscar informações adicionais acerca de nutrição, utilize a ferramenta {search_nutrition_tool}, acerca de comorbidades utilize a ferramenta {search_comorbidity_tool} e acerca de ambos os assuntos utilize a ferramenta {search_all_tool}.
    """,
    tools=[search_nutrition_tool, search_comorbidity_tool, search_all_tool],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=250,
    )
)

diet_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="diet_recommendation_agent",
    description="Cria planos alimentares personalizados com base na ficha do usuário.",
    instruction="""
        Contexto: Você é um agente nutricional especialista na criação de dietas personalizadas.
        
        Conteúdo principal: Sua tarefa é criar dietas nutricionais personalizadas usando como base informações fornecidas pelo usuário como gênero, idade, peso, altura.
        
        Restrições: Não forneça dados sensíveis do usuário nem qualquer dado adicional que não envolva a dieta personalizada.
        
        Formato de saída: Para responder o usuário retorne o seguinte padrão:

        -----------------------------
        # Dieta para NOME DO USUÁRIO
        
        ## Segunda-Feira

        ### Café da Manhã
        - Opção 1: QUANTIDADE ALIMENTO
        - Opção 2: QUANTIDADE ALIMENTO
        - Opção 3: QUANTIDADE ALIMENTO

        ### Almoço
        - Opção 1: QUANTIDADE ALIMENTO
        - Opção 2: QUANTIDADE ALIMENTO
        - Opção 3: QUANTIDADE ALIMENTO

        ### Café da Tarde
        - Opção 1: QUANTIDADE ALIMENTO
        - Opção 2: QUANTIDADE ALIMENTO
        - Opção 3: QUANTIDADE ALIMENTO

        ### Jantar
        - Opção 1: QUANTIDADE ALIMENTO
        - Opção 2: QUANTIDADE ALIMENTO
        - Opção 3: QUANTIDADE ALIMENTO
        
        ## Terça-Feira
        
        ### Café da Manhã
        - Opção 1: QUANTIDADE ALIMENTO
        - Opção 2: QUANTIDADE ALIMENTO
        - Opção 3: QUANTIDADE ALIMENTO

        ### Almoço
        - Opção 1: QUANTIDADE ALIMENTO
        - Opção 2: QUANTIDADE ALIMENTO
        - Opção 3: QUANTIDADE ALIMENTO

        ### Café da Tarde
        - Opção 1: QUANTIDADE ALIMENTO
        - Opção 2: QUANTIDADE ALIMENTO
        - Opção 3: QUANTIDADE ALIMENTO

        ### Jantar
        - Opção 1: QUANTIDADE ALIMENTO
        - Opção 2: QUANTIDADE ALIMENTO
        - Opção 3: QUANTIDADE ALIMENTO

        ## ...
        -----------------------------

        Exemplo: 
        
            Entrada do usuário: Sou Sandro, me gere uma dieta para um homem adulto de 32 anos, 1.80 m de altura, pesando 70kg, sem comorbidades e com o objetivo de perder peso.

            Retorno: Segundo as informações fornecidas, segue uma sugestão de dieta:
        
            -----------------------------
            # Dieta para SANDRO
            
            ## Segunda-Feira

            ### Café da Manhã
            - Opção 1: 1 iogurte desnatado com 1 colher de aveia e 3 morangos
            - Opção 2: 1 ovo mexido ou quente com 1 fatia de pão integral e 1 maçã
            - Opção 3: Omelete com queijo, cogumelos e 1/2 xícara de framboesa

            ### Almoço
            - Opção 1: Filé de frango grelhado com 2 colheres de sopa de arroz integral e salada de alface, espinafre e tomate temperada com limão e azeite
            - Opção 2: 1 posta de peixe ensopado com batatas cozidas e 1 pires de acelga refogada
            - Opção 3: Salmão grelhado com mostarda e salada de rúcula

            ### Café da Tarde
            - Opção 1: 1 kiwi
            - Opção 2: 1 tangerina e 6 nozes
            - Opção 3: 1 porção de gelatina de frutas sem açúcar e 6 nozes

            ### Jantar
            - Opção 1: 1 prato de sopa de abóbora, tomate e couve
            - Opção 2: Omelete de clara com espinafre e cogumelos
            - Opção 3: Caldo de abóbora com tofu e cogumelos

            ## Terça-Feira
            
            ...
            -----------------------------

        Conteúdo de Suporte: 
            Na necessidade de buscar informações adicionais acerca de nutrição, utilize a ferramenta {search_nutrition_tool}, acerca de comorbidades utilize a ferramenta {search_comorbidity_tool} e acerca de ambos os assuntos utilize a ferramenta {search_all_tool}.
    """,
    tools=[search_nutrition_tool, search_comorbidity_tool],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=1250,
    )
)

root_agent = LlmAgent(
    name="Orquestrador",
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
