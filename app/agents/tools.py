from google.adk.tools import FunctionTool
from pathlib import Path
import yaml
import chromadb

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR.parent.parent / "configurations/policies.yaml"  
DB_PATH = BASE_DIR.parent.parent / "docs" / "my_db"  
client = chromadb.PersistentClient(path=DB_PATH)

nutrition = client.get_or_create_collection(name="nutrition")
comorbidity = client.get_or_create_collection(name="comorbidity")

def load_policies() -> dict:
    """
    Carrega o arquivo de políticas do sistema.
    """
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)
    
load_policies_tool = FunctionTool(func=load_policies)

def search_nutrition(query: str):
    """Search for nutrition-related information."""
    results = nutrition.query(
        query_texts=[query], 
        n_results=5,
    )
    texts = [item for sublist in results['documents'] for item in sublist]
    return "\n".join(texts)

search_nutrition_tool = FunctionTool(func=search_nutrition)

def search_comorbidity(query: str):
    """Search for comorbidity-related information."""
    results = comorbidity.query(
        query_texts=[query], 
        n_results=5,
    )
    texts = [item for sublist in results['documents'] for item in sublist]
    return "\n".join(texts)

search_comorbidity_tool = FunctionTool(func=search_comorbidity)

def search_all(query: str):
    """Search for both nutrition and comorbidity-related information."""
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

search_all_tool = FunctionTool(func=search_all)

def search_food(query: str):
    """Search for food-related information."""
    results = nutrition.query(
        query_texts=[query], 
        n_results=5,
    )
    texts = [item for sublist in results['documents'] for item in sublist]
    return "\n".join(texts)

search_food_tool = FunctionTool(func=search_food)