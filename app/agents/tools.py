from google.adk.tools import FunctionTool
from typing import List, Optional
from dotenv import load_dotenv
from pathlib import Path
import chromadb
import requests
import yaml
import json
import os


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR.parent.parent / "configurations/policies.yaml"  
DB_PATH = BASE_DIR.parent.parent / "docs" / "my_db"  
client = chromadb.PersistentClient(path=DB_PATH)

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL")

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

from app.context import jwt_token_ctx

def create_anamnese(data: dict):
    """
    Cria um novo documento de anamnese no backend (MongoDB).
    Espera um dicionário com os campos da anamnese preenchidos.
    """
    try:
        # Obter o token do contexto
        token = jwt_token_ctx.get()
        
        if not token:
            return "Erro: Token de autenticação não encontrado. Certifique-se de enviar o header Authorization."
        
        # Converter listas para strings se necessário
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = [str(v) for v in value]
        print("---------------------")
        print(data)
        print("---------------------")

        # Incluir o token JWT no header
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(API_BASE_URL, headers=headers, data=json.dumps(data))

        print("Response Status Code:")
        print(response.status_code)

        if response.status_code == 201:
            return f"Anamnese salva com sucesso! ID: {response.json().get('id', 'desconhecido')}"
        elif response.status_code == 401:
            return "Erro de autenticação: Token JWT inválido ou expirado."
        elif response.status_code == 403:
            return "Erro de autorização: Você não tem permissão para realizar esta ação."
        else:
            return f"Erro ao salvar anamnese ({response.status_code}): {response.text}"

    except Exception as e:
        return f"Erro inesperado ao salvar anamnese: {str(e)}"

create_anamnese_tool = FunctionTool(func=create_anamnese)

def get_anamneses():
    """
    Recupera todos os documentos de anamnese do backend (MongoDB).
    """
    try:
        # Obter o token do contexto
        token = jwt_token_ctx.get()
        
        if not token:
            return "Erro: Token de autenticação não encontrado. Certifique-se de enviar o header Authorization."
        
        # Incluir o token JWT no header
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(API_BASE_URL, headers=headers)

        print(response.json())

        if response.status_code == 200:
            return response.json()  # Retorna a lista de anamneses
        elif response.status_code == 401:
            return "Erro de autenticação: Token JWT inválido ou expirado."
        elif response.status_code == 403:
            return "Erro de autorização: Você não tem permissão para realizar esta ação."
        else:
            return f"Erro ao recuperar anamneses ({response.status_code}): {response.text}"

    except Exception as e:
        return f"Erro inesperado ao recuperar anamneses: {str(e)}"

get_anamneses_tool = FunctionTool(func=get_anamneses)

def update_anamnesis_state(
    birthDate: Optional[str] = None,
    sex: Optional[str] = None,
    occupation: Optional[str] = None,
    consultationReason: Optional[str] = None,
    healthConditions: Optional[List[str]] = None,
    allergies: Optional[List[str]] = None,
    surgeries: Optional[List[str]] = None,
    activityType: Optional[str] = None,
    activityFrequency: Optional[str] = None,
    activityDuration: Optional[str] = None,
    sleepQuality: Optional[str] = None,
    wakeDuringNight: Optional[str] = None,
    bowelFrequency: Optional[str] = None,
    stressLevel: Optional[str] = None,
    alcoholConsumption: Optional[str] = None,
    smoking: Optional[str] = None,
    hydrationLevel: Optional[str] = None,
    takesMedication: Optional[str] = None,
    medicationDetails: Optional[str] = None,
    tool_context = None
):
    """
    Atualiza o session.state com novos dados da anamnese.
    Passe apenas os campos que foram fornecidos pelo paciente.
    """
    
    print("="*50)
    print("DEBUG - update_anamnesis_state called")
    
    # Coleta todos os argumentos não-None
    updates = {}
    params = {
        "birthDate": birthDate,
        "sex": sex,
        "occupation": occupation,
        "consultationReason": consultationReason,
        "healthConditions": healthConditions,
        "allergies": allergies,
        "surgeries": surgeries,
        "activityType": activityType,
        "activityFrequency": activityFrequency,
        "activityDuration": activityDuration,
        "sleepQuality": sleepQuality,
        "wakeDuringNight": wakeDuringNight,
        "bowelFrequency": bowelFrequency,
        "stressLevel": stressLevel,
        "alcoholConsumption": alcoholConsumption,
        "smoking": smoking,
        "hydrationLevel": hydrationLevel,
        "takesMedication": takesMedication,
        "medicationDetails": medicationDetails
    }
    
    for key, value in params.items():
        if value is not None:
            updates[key] = value
    
    print(f"Updates received: {updates}")
    
    # Atualiza o session.state
    if tool_context and hasattr(tool_context, 'session'):
        session = tool_context.session
        print(f"Session state before update: {dict(session.state)}")
        
        for key, value in updates.items():
            session.state[key] = value
        
        print(f"Session state after update: {dict(session.state)}")
    else:
        print("WARNING: tool_context or session not available")
    
    # Verifica campos faltantes
    required_fields = list(params.keys())
    missing_fields = []
    filled_fields = {}
    
    if tool_context and hasattr(tool_context, 'session'):
        for field in required_fields:
            value = tool_context.session.state.get(field)
            if value in (None, "", [], {}):
                missing_fields.append(field)
            else:
                filled_fields[field] = value
    
    print(f"Missing fields: {missing_fields}")
    print(f"Filled fields count: {len(filled_fields)}/{len(required_fields)}")
    print("="*50)
    
    return {
        "success": True,
        "message": f"Atualizados {len(updates)} campo(s). Faltam {len(missing_fields)} campo(s).",
        "updated_fields": list(updates.keys()),
        "missing_fields": missing_fields,
        "filled_fields": filled_fields
    }

update_anamnesis_state_tool = FunctionTool(func=update_anamnesis_state)

def search_food(query: str):
    """Search for food-related information."""
    results = nutrition.query(
        query_texts=[query], 
        n_results=5,
    )
    texts = [item for sublist in results['documents'] for item in sublist]
    return "\n".join(texts)

search_food_tool = FunctionTool(func=search_food)