from llama_cpp import Llama
from dotenv import load_dotenv
import os
import time

load_dotenv()

class MedGemmaClient:
    def __init__(self,
                 repo_id: str = "unsloth/medgemma-4b-it-GGUF",
                 filename: str = "medgemma-4b-it-BF16.gguf",
                 n_ctx: int = 512,
                 n_threads: int = None):
        print("Downloading/Loading MedGemma from Hugging Face Hub...")
        self.model = Llama.from_pretrained(
            repo_id=repo_id,
            filename=filename,
            hf_token=os.getenv("HF_TOKEN"),
            n_ctx=n_ctx,
            n_threads=n_threads or os.cpu_count(),
            verbose=False
        )
        print("MedGemma loaded successfully!")

    def generate(self, prompt: str, max_new_tokens=120, temperature=0.3, top_p=0.9) -> str:
        start_time = time.time()
        output = self.model(
            prompt,
            max_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=["</s>"]
        )
        elapsed = time.time() - start_time
        print(f"Response time: {elapsed:.2f} seconds.")
        return output["choices"][0]["text"].strip()
