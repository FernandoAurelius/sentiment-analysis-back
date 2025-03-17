from google import genai
import os
from nlpcloud import Client
from os.path import join, dirname
from dotenv import load_dotenv
import logging
import time

logger = logging.getLogger(__name__)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
logger.info("Variáveis de ambiente carregadas")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
NLP_API_KEY = os.getenv("NLPCLOUD_API_KEY")

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY não encontrada nas variáveis de ambiente")
if not NLP_API_KEY:
    logger.warning("NLP_API_KEY não encontrada nas variáveis de ambiente")

def create_juice(message_text, prompt):
    logger.info(f"Gerando conteúdo com Gemini API: mensagem de {len(message_text)} caracteres")
    start_time = time.time()
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=f"{prompt}: {message_text}"
        )
        end_time = time.time()
        logger.info(f"Resposta do Gemini recebida em {end_time - start_time:.2f} segundos")
        return response
    except Exception as e:
        logger.error(f"Erro ao chamar a API Gemini: {str(e)}")
        raise

# Função para analisar o sentimento de uma frase
def analyze_phrase(phrase: str):
    logger.info(f"Analisando sentimento da frase: '{phrase[:50]}...' (tamanho: {len(phrase)} caracteres)")
    start_time = time.time()
    
    try:
        # Usa a API da NLP Cloud para fazer a análise de sentimentos na nuvem
        # Isso resolve a latência absurda que estávamos enfrentando antes (o modelo estava rodando localmente)
        analyst = Client("distilbert-base-uncased-finetuned-sst-2-english", api_key=NLP_API_KEY, lang="por_Latn")
        response = analyst.sentiment(phrase)
        
        logger.debug(f"Resposta bruta da API NLPCloud: {response}")
        
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
            logger.info(f"Sentimento detectado: {item['label']} com score {item['score']}")
        else:
            logger.warning("Formato de resposta inesperado da API NLPCloud, usando fallback")
            formatted_response.append({
                "label": "UNDEFINED",
                "score": 0.0
            })
        
        end_time = time.time()
        logger.info(f"Análise de sentimento concluída em {end_time - start_time:.2f} segundos")
        
        return formatted_response
    except Exception as e:
        logger.error(f"Erro na análise de sentimento: {str(e)}")
        # Retorna um fallback em caso de erro
        return [{"label": "ERROR", "score": 0.0}]
