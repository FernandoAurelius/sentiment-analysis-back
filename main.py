from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.analysis_request import AnalysisRequest
from pydantic import BaseModel
import logging
import time
import os

# Configuração do sistema de logging
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_directory}/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Iniciando aplicação de análise de sentimentos")

class Message(BaseModel):
    message: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "https://sentiment.floresdev.com.br"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Middleware CORS configurado")

@app.post("/analyze")
def analyze_sentiment(message_list: list[Message]):
    start_time = time.time()
    logger.info(f"Nova requisição recebida com {len(message_list)} mensagens")
    
    message_texts = [message.message for message in message_list]
    logger.debug(f"Mensagens para análise: {message_texts}")
    
    analysis = AnalysisRequest(message_texts)
    result = {"analysis": analysis.dict()}
    
    end_time = time.time()
    logger.info(f"Análise concluída em {end_time - start_time:.2f} segundos")
    return result
