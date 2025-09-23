from llama_cpp import Llama  # Llama was chosen to run the quantized .gguf model for better performance.
from dotenv import load_dotenv
import os
import time

load_dotenv()

class MedGemmaClient:
    _instance = None

    def __new__(cls,
                repo_id: str = "unsloth/medgemma-4b-it-GGUF",
                filename: str = "medgemma-4b-it-BF16.gguf",
                n_ctx: int = 1024,
                n_threads: int = None):

        if cls._instance is None:
            cls._instance = super().__new__(cls)

            print(" Downloading/Loading MedGemma from the Hugging Face Hub...")

            cls._instance.model = Llama.from_pretrained(
            repo_id="unsloth/medgemma-4b-it-GGUF",
            filename="medgemma-4b-it-BF16.gguf",
            hf_token=os.getenv("HF_TOKEN"),  
            n_ctx=n_ctx,
            n_threads=n_threads or os.cpu_count(),
            verbose=False
        )

            print("MedGemma (GGUF)")

        return cls._instance

    def generate(
            self, prompt: str,
            max_new_tokens: int = 512,
            temperature: float = 0.3,
            top_p: float = 0.9
        ) -> str:

        start_time = time.time()
        output = self.model(
            prompt,
            max_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=["</s>"]
        )
        end_time = time.time()
        elapsed = end_time - start_time

        print(f"Response time: {elapsed:.2f} seconds.")

        return output["choices"][0]["text"].strip()


# Usage example
if __name__ == "__main__":
    client = MedGemmaClient()

    response = client.generate("Explique o que é gripe.")
    print(response)

# The first run usually has a longer response time.