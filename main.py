from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from models.analysis_request import AnalysisRequest
from pydantic import BaseModel
import logging
import time
import os
import traceback
import json

# Configuração do sistema de logging
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{log_directory}/app.log"),
        logging.StreamHandler(),  # Redireciona as mensagens para o console
    ],
)

logger = logging.getLogger(__name__)
logger.info("Iniciando aplicação de análise de sentimentos")


class Message(BaseModel):
    """
    Modelo de dados para mensagens recebidas pelo front-end na requisição de análise.\n
    Basicamente, é uma lista de objetos contendo uma string no formato:
    ```
        [
            {"message": "Primeira mensagem"},
            {"message": "Segunda mensagem"},
            {"message": "Terceira mensagem"},
        ]
    ```
    """
    message: str


app = FastAPI()

# Lista expandida de origens permitidas
origins = [
    "http://localhost:5173",
    "https://sentiment.floresdev.com.br",
    "http://sentiment.floresdev.com.br",
]

# Configuração CORS clara e explícita
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Type"],
    max_age=86400,  # Cache por 24 horas para reduzir preflight requests
)

logger.info(f"Middleware CORS configurado para origens: {origins}")


# Handler para erros de validação de requisição
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_detail = exc.errors()
    logger.error(f"Erro de validação de requisição: {error_detail}")

    # Log do corpo da requisição para diagnóstico
    body = await request.body()
    try:
        body_str = body.decode()
        logger.error(f"Corpo da requisição com erro: {body_str}")
    except:
        logger.error(f"Não foi possível decodificar o corpo da requisição")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": error_detail,
            "message": "Erro na validação dos dados de entrada",
        },
    )


# Middleware para logging de todas as requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log da requisição recebida
    logger.info(f"Requisição recebida: {request.method} {request.url}")

    # Tenta ler e registrar o corpo da requisição
    try:
        body = await request.body()
        body_str = body.decode()
        if len(body_str) > 0:
            logger.info(
                f"Corpo da requisição: {body_str[:1000]}{'...' if len(body_str) > 1000 else ''}"
            )

        # Precisa reconstruir o corpo da requisição para uso posterior
        request._body = body
    except Exception as e:
        logger.error(f"Erro ao ler corpo da requisição: {str(e)}")

    # Processa a requisição
    response = await call_next(request)

    # Log da resposta
    process_time = time.time() - start_time
    logger.info(
        f"Requisição processada em {process_time:.2f}s com status {response.status_code}"
    )

    return response


# Endpoint simples para verificar se o servidor está funcionando
@app.get("/health")
def health_check():
    logger.info("Verificação de saúde realizada")
    return {
        "status": "online",
        "message": "API de análise de sentimentos está operacional",
    }


@app.post("/analyze")
async def analyze_sentiment(message_list: list[Message]):
    """
    Recebe requisições de análise de sentimento do front-end 
    Loga informações relacionadas ao processamento da requisição
    Retorna o resultado da análise em formato de dicionário, que depois é convertido para JSON.
    """
    start_time = time.time()
    logger.info(
        f"Nova requisição de análise recebida com {len(message_list)} mensagens"
    )

    try:
        message_texts = [message.message for message in message_list]
        logger.debug(f"Mensagens para análise: {message_texts}")

        analysis = AnalysisRequest(message_texts)
        result = {"analysis": analysis.dict()}

        end_time = time.time()
        logger.info(
            f"Análise concluída com sucesso em {end_time - start_time:.2f} segundos"
        )
        return result
    except Exception as e:
        logger.error(f"Erro durante a análise: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": str(e),
                "message": "Ocorreu um erro ao processar sua solicitação",
            },
        )


# Endpoint para debug - mostra exatamente o que foi recebido
@app.post("/debug")
async def debug_request(request: Request):
    body = await request.body()
    body_str = body.decode()

    try:
        # Tenta analisar o corpo como JSON
        json_body = json.loads(body_str)
        is_valid = True
    except:
        is_valid = False

    headers = dict(request.headers)

    logger.info(f"Debug request recebido: {body_str}")

    return {
        "received_data": body_str,
        "is_valid_json": is_valid,
        "parsed_json": json_body if is_valid else None,
        "headers": headers,
        "method": request.method,
        "url": str(request.url),
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
