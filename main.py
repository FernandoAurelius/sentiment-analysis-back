from fastapi import FastAPI

from models.analysis_request import AnalysisRequest

from pydantic import BaseModel

class Message(BaseModel):
    message: str

app = FastAPI()

@app.post("/analyze")
def analyze_sentiment(message_list: list[Message]):
    message_texts = [message.message for message in message_list]
    analysis = AnalysisRequest(message_texts)
    return {"analysis": analysis.dict()}
