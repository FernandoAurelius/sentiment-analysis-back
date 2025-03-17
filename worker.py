import time
import logging
import os
from services import process_pending_tasks

# Configuração do sistema de logging
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_directory}/worker.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Iniciando worker para processamento de análises assíncronas")
    try:
        process_pending_tasks()
    except KeyboardInterrupt:
        logger.info("Worker interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal no worker: {str(e)}")
