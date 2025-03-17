from google import genai
import os
from nlpcloud import Client
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

NLP_API_KEY = os.getenv("NLPCLOUD_API_KEY")

def create_juice(message_text, prompt):
    client = genai.Client(api_key=GEMINI_API_KEY)
    # Mesma coisa que: 
    # response = client.models.generate_content(etc.)
    # return response
    return client.models.generate_content(
        model="gemini-2.0-flash", contents=f"{prompt}: {message_text}"
    )

# Função para analisar o sentimento de uma frase
def analyze_phrase(phrase: str):
    # Usa a API da NLP Cloud para fazer a análise de sentimentos na nuvem
    # Isso resolve a latência absurda que estávamos enfrentando antes (o modelo estava rodando localmente)
    analyst = Client("distilbert-base-uncased-finetuned-sst-2-english", api_key=NLP_API_KEY, lang="por_Latn")
    response = analyst.sentiment(phrase)
    
    # Adapta a resposta da API para o formato esperado pelo restante do código
    # O formato anterior esperava uma lista onde cada item tem 'label' e 'score',
    # pois estávamos usando um transformador local
    formatted_response = []
    
    if "scored_labels" in response:
        item = response["scored_labels"][0]
        formatted_response.append({
            "label": item["label"],
            "score": item["score"]
        })
    else:
        formatted_response.append({
            "label": "UNDEFINED",
            "score": 0.0
        })
    
    return formatted_response
