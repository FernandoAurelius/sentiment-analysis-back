from google import genai
import os
from transformers import pipeline
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

API_KEY = os.getenv("GEMINI_API_KEY") 


def create_juice(message_text, prompt):
    client = genai.Client(api_key=API_KEY)
    # Mesma coisa que: 
    # response = client.models.generate_content(etc.)
    # return response
    return client.models.generate_content(
        model="gemini-2.0-flash", contents=f"{prompt}: {message_text}"
    )

# Função para analisar o sentimento de uma frase
def analyze_phrase(phrase: str):
    # Cria a pipeline de análise de sentimentos usando um modelo multilingue
    analyst = pipeline(
        "sentiment-analysis", 
        model="nlptown/bert-base-multilingual-uncased-sentiment"
    )
    return analyst(phrase)
    