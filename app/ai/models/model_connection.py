from dotenv import load_dotenv
import os
import time

# Usando a importação da biblioteca legada
import google.generativeai as genai
# Importar o tipo de configuração (GenerationConfig)
# Nota: Esta importação é crucial, mas pode ser desnecessária em versões muito antigas
from google.generativeai.types import GenerationConfig 

load_dotenv()

class GeminiClient:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model_name = model
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("É necessário definir GOOGLE_API_KEY no .env")
        
        # 🔑 CORREÇÃO ESSENCIAL: Configure a API Key GLOBALMENTE.
        # Isto é necessário porque a sua versão de GenerativeModel não aceita 'api_key'
        # no construtor.
        genai.configure(api_key=self.api_key)
        
        # Agora inicializamos o modelo, passando APENAS o nome do modelo.
        self.model_client = genai.GenerativeModel(
            model_name=self.model_name
            # Removido: api_key=self.api_key
        )
        
        print(f"✅ Cliente Gemini inicializado para o modelo {self.model_name}")

    def generate(self, prompt: str, max_output_tokens: int = 1024, temperature: float = 0.4) -> str:
        start_time = time.time()

        # Chamamos o método generate_content no cliente instanciado.
        # A chave de API já está configurada globalmente.
        response = self.model_client.generate_content(
            contents=prompt,
            config=GenerationConfig(
                max_output_tokens=max_output_tokens,
                temperature=temperature
            )
        )

        elapsed = time.time() - start_time
        print(f"🕒 Tempo de resposta: {elapsed:.2f}s")
        return response.text

# Teste de conexão (função síncrona)
def test_connection():
    try:
        client = GeminiClient()
        print("✅ Conexão com Gemini estabelecida!")

        prompt = "Explique o que é aprendizado de máquina em uma frase."
        response = client.generate(prompt, max_output_tokens=128)
        print(f"\n📨 Prompt: {prompt}\n")
        print(f"🤖 Resposta do modelo:\n{response}")

    except Exception as e:
        print(f"❌ Falha ao conectar ou gerar resposta: {type(e).__name__}: {e}")

if __name__ == "__main__":
    if os.getenv("GOOGLE_API_KEY"):
        test_connection()
    else:
        print("🛑 Erro: GOOGLE_API_KEY não foi encontrada. Verifique seu arquivo .env.")