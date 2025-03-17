from google import genai
import os
from nlpcloud import Client
from os.path import join, dirname
from dotenv import load_dotenv
import logging
import time
import json
import redis
import uuid
import random
import threading

logger = logging.getLogger(__name__)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
logger.info("Variáveis de ambiente carregadas")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
NLP_API_KEY = os.getenv("NLPCLOUD_API_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_QUEUE_KEY = "sentiment_analysis_queue"
REDIS_RESULTS_KEY = "sentiment_analysis_results:"

# Configurações para gerenciamento de rate limiting
GEMINI_MAX_REQUESTS_PER_MINUTE = int(os.getenv("GEMINI_MAX_REQUESTS_PER_MINUTE", 5))
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", 3))
GEMINI_RETRY_DELAY_BASE = float(os.getenv("GEMINI_RETRY_DELAY_BASE", 2.0))

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY não encontrada nas variáveis de ambiente")
if not NLP_API_KEY:
    logger.warning("NLP_API_KEY não encontrada nas variáveis de ambiente")

# Conexão com Redis
redis_client = None

# Lock para controlar concorrência nas chamadas do Gemini
gemini_lock = threading.Lock()
gemini_last_request_time = 0
gemini_request_count = 0
gemini_request_window_start = 0

def get_redis_connection():
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
            redis_client.ping()  # Verificar conexão
            logger.info(f"Conexão com Redis estabelecida em {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.error(f"Erro ao conectar com Redis: {str(e)}")
            redis_client = None
    return redis_client

def reset_gemini_rate_limit_window():
    """Reset a janela de contagem de requests do Gemini se necessário"""
    global gemini_request_window_start, gemini_request_count
    current_time = time.time()
    
    # Se já passou mais de um minuto desde o início da janela atual
    if current_time - gemini_request_window_start >= 60:
        gemini_request_window_start = current_time
        gemini_request_count = 0
        logger.debug("Janela de rate limiting do Gemini reiniciada")

def can_make_gemini_request():
    """Verifica se podemos fazer uma nova request para o Gemini dentro do rate limit"""
    global gemini_request_count, gemini_request_window_start
    
    with gemini_lock:
        current_time = time.time()
        
        # Inicializa a janela se for a primeira request
        if gemini_request_window_start == 0:
            gemini_request_window_start = current_time
            gemini_request_count = 0
            return True
        
        # Verifica se precisamos reiniciar a janela
        reset_gemini_rate_limit_window()
        
        # Verifica se estamos dentro do limite
        if gemini_request_count < GEMINI_MAX_REQUESTS_PER_MINUTE:
            gemini_request_count += 1
            logger.debug(f"Request Gemini permitida: {gemini_request_count}/{GEMINI_MAX_REQUESTS_PER_MINUTE} na janela atual")
            return True
        else:
            time_until_reset = 60 - (current_time - gemini_request_window_start)
            logger.warning(f"Rate limit do Gemini atingido. Próxima janela em {time_until_reset:.1f}s")
            return False

def create_juice(message_text, prompt, cache_key=None):
    """
    Gera conteúdo usando a API Gemini com suporte para cache, rate limiting e retry
    
    Args:
        message_text: Texto da mensagem para análise
        prompt: Prompt para o modelo Gemini
        cache_key: Chave opcional para cache no Redis
    
    Returns:
        Resposta da API Gemini
    """
    logger.info(f"Gerando conteúdo com Gemini API: mensagem de {len(message_text)} caracteres")
    start_time = time.time()
    
    # Tenta obter do cache primeiro se cache_key foi fornecido
    if cache_key and get_redis_connection():
        redis_conn = get_redis_connection()
        cached_result = redis_conn.get(cache_key)
        if cached_result:
            logger.info(f"Resultado encontrado no cache para {cache_key[:20]}...")
            return json.loads(cached_result)
    
    # Implementação de retry com backoff exponencial
    retry_count = 0
    last_exception = None
    
    while retry_count <= GEMINI_MAX_RETRIES:
        try:
            # Verifica se podemos fazer uma nova requisição (rate limiting)
            wait_time = 0
            while not can_make_gemini_request():
                wait_time = random.uniform(1, 3)  # Adiciona um pouco de jitter
                logger.info(f"Aguardando {wait_time:.1f}s antes de nova tentativa (rate limiting)")
                time.sleep(wait_time)
            
            # Faz a chamada para a API
            logger.debug(f"Fazendo requisição para API Gemini (tentativa {retry_count + 1}/{GEMINI_MAX_RETRIES + 1})")
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-1.5-flash", 
                contents=f"{prompt}: {message_text}"
            )
            
            # Salva no cache se temos uma chave e conexão Redis
            if cache_key and get_redis_connection():
                redis_conn = get_redis_connection()
                redis_conn.set(cache_key, json.dumps(response.text))
                redis_conn.expire(cache_key, 3600)  # Expira em 1 hora
                logger.debug(f"Resultado armazenado no cache com chave {cache_key[:20]}...")
            
            end_time = time.time()
            logger.info(f"Resposta do Gemini recebida em {end_time - start_time:.2f} segundos")
            return response
        
        except Exception as e:
            last_exception = e
            retry_count += 1
            
            if retry_count <= GEMINI_MAX_RETRIES:
                # Calcula tempo de espera com backoff exponencial e jitter
                delay = GEMINI_RETRY_DELAY_BASE ** retry_count + random.uniform(0, 1)
                logger.warning(f"Erro na chamada à API Gemini: {str(e)}. Tentativa {retry_count}/{GEMINI_MAX_RETRIES}. Aguardando {delay:.1f}s.")
                time.sleep(delay)
            else:
                logger.error(f"Todas as tentativas falharam para chamada Gemini. Último erro: {str(e)}")
                raise last_exception
    
    # Se chegamos aqui, todas as tentativas falharam
    logger.error(f"Falha após {GEMINI_MAX_RETRIES} tentativas. Último erro: {str(last_exception)}")
    raise last_exception

# Função para analisar o sentimento de uma frase
def analyze_phrase(phrase: str):
    logger.info(f"Analisando sentimento da frase: '{phrase[:50]}...' (tamanho: {len(phrase)} caracteres)")
    start_time = time.time()
    
    try:
        # Usa a API da NLP Cloud para fazer a análise de sentimentos na nuvem
        analyst = Client("finetuned-llama-3-70b", token=NLP_API_KEY, gpu=True)
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

# Funções assíncronas com Redis

def queue_analysis_task(phrase: str) -> str:
    """
    Adiciona uma tarefa de análise de sentimento à fila Redis
    Retorna um ID de tarefa para acompanhamento
    """
    task_id = str(uuid.uuid4())
    redis_conn = get_redis_connection()
    
    if redis_conn:
        try:
            task_data = {
                "id": task_id,
                "phrase": phrase,
                "status": "pending",
                "timestamp": time.time()
            }
            
            # Adiciona à fila de tarefas a serem processadas
            redis_conn.lpush(REDIS_QUEUE_KEY, json.dumps(task_data))
            
            # Inicializa o resultado com status pendente
            result_key = f"{REDIS_RESULTS_KEY}{task_id}"
            redis_conn.set(result_key, json.dumps({"status": "pending"}))
            redis_conn.expire(result_key, 3600)  # Expira em 1 hora
            
            logger.info(f"Tarefa {task_id} adicionada à fila")
            return task_id
        except Exception as e:
            logger.error(f"Erro ao adicionar tarefa à fila Redis: {str(e)}")
            raise
    else:
        # Fallback para processamento síncrono se Redis não estiver disponível
        logger.warning("Redis indisponível, realizando análise de forma síncrona")
        result = analyze_phrase(phrase)
        return json.dumps({"result": result, "sync": True})

def get_analysis_result(task_id: str):
    """
    Obtém o resultado de uma tarefa de análise pelo ID
    """
    redis_conn = get_redis_connection()
    if not redis_conn:
        return {"error": "Redis não disponível", "status": "error"}
    
    try:
        result_key = f"{REDIS_RESULTS_KEY}{task_id}"
        result_json = redis_conn.get(result_key)
        
        if not result_json:
            return {"status": "not_found"}
            
        return json.loads(result_json)
    except Exception as e:
        logger.error(f"Erro ao obter resultado da tarefa {task_id}: {str(e)}")
        return {"error": str(e), "status": "error"}

def process_pending_tasks():
    """
    Função para processamento em background das tarefas pendentes
    Esta função deve ser executada em um worker separado
    """
    redis_conn = get_redis_connection()
    if not redis_conn:
        logger.error("Redis não disponível para processamento de tarefas")
        return
    
    logger.info("Iniciando processamento de tarefas pendentes")
    
    while True:
        try:
            # Obtém uma tarefa da fila (espera até 1 segundo)
            task_json = redis_conn.brpop(REDIS_QUEUE_KEY, 1)
            
            # Se não há tarefas, continua o loop
            if not task_json:
                continue
                
            # Extrai a tarefa
            _, task_data_json = task_json
            task_data = json.loads(task_data_json)
            task_id = task_data["id"]
            phrase = task_data["phrase"]
            
            logger.info(f"Processando tarefa {task_id}")
            
            # Atualiza status para "processando"
            result_key = f"{REDIS_RESULTS_KEY}{task_id}"
            redis_conn.set(result_key, json.dumps({
                "status": "processing",
                "updated_at": time.time()
            }))
            
            # Executa a análise
            try:
                analysis_result = analyze_phrase(phrase)
                
                # Armazena o resultado
                result = {
                    "status": "completed",
                    "result": analysis_result,
                    "completed_at": time.time()
                }
                redis_conn.set(result_key, json.dumps(result))
                redis_conn.expire(result_key, 3600)  # Mantém o resultado por 1 hora
                
                logger.info(f"Tarefa {task_id} concluída com sucesso")
            except Exception as e:
                # Em caso de erro, armazena a informação do erro
                error_result = {
                    "status": "error",
                    "error": str(e),
                    "completed_at": time.time()
                }
                redis_conn.set(result_key, json.dumps(error_result))
                redis_conn.expire(result_key, 3600)
                
                logger.error(f"Erro ao processar tarefa {task_id}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Erro no worker de processamento: {str(e)}")
            # Pequena pausa para evitar consumo excessivo de CPU em caso de erros repetidos
            time.sleep(1)
