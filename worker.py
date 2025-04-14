import logging
import os
import time

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

# Este arquivo está desativado já que não usamos mais Redis para o processamento assíncrono.
# Mantido para referência futura.

if __name__ == "__main__":
    logger.info("Worker desativado - processamento assíncrono não está disponível sem Redis")
    logger.info("Todas as operações agora são síncronas")
