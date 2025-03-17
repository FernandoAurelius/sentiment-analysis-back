from services import analyze_phrase
import logging
import time

logger = logging.getLogger(__name__)

class MessageEvaluation:
    message_text: str
    label: str
    score: float
    
    def __init__(self, message_text):
        logger.info(f"Avaliando mensagem: '{message_text[:30]}...' ({len(message_text)} caracteres)")
        start_time = time.time()
        
        self.message_text = message_text
        try:
            evaluation = analyze_phrase(message_text)
            self.label = evaluation[0]['label']
            self.score = evaluation[0]['score']
            logger.info(f"Resultado da avaliação: {self.label} (score: {self.score})")
        except Exception as e:
            logger.error(f"Erro ao avaliar mensagem: {str(e)}")
            self.label = "ERROR"
            self.score = 0.0
            
        logger.info(f"Avaliação concluída em {time.time() - start_time:.2f} segundos")
        
    def dict(self):
        return {
            "message_text": self.message_text,
            "label": self.label,
            "score": self.score
        }
