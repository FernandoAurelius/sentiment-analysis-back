from services import analyze_phrase


class MessageEvaluation:
    message_text: str
    label: str
    score: float
    
    def __init__(self, message_text):
        self.message_text = message_text
        self.label = analyze_phrase(message_text)[0]['label']
        self.score = analyze_phrase(message_text)[0]['score']
        
    def dict(self):
        return {
            "message_text": self.message_text,
            "label": self.label,
            "score": self.score
        }
    