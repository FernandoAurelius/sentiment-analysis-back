from models.message_evaluation import MessageEvaluation
from services import create_juice


class AnalysisRequest:
    process_description: list[str]
    poem: list[str]
    message_list: list[MessageEvaluation]
    
    def __init__(self, message_list):
        self.message_list = [MessageEvaluation(message) for message in message_list]
        self.process_description = [create_juice(message, "Crie uma descrição do processo de análise de sentimentos com base na seguinte mensagem:").text for message in message_list]
        self.poem = [create_juice(message, "Crie um poema com base na seguinte mensagem:").text for message in message_list]
        
    def dict(self):
        return {
            "process_description": self.process_description,
            "poem": self.poem,
            "message_list": [message.dict() for message in self.message_list]
        }
     