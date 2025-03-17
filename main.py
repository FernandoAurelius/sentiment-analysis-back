from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from models.analysis_request import AnalysisRequest

from pydantic import BaseModel


class Message(BaseModel):
    message: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "https://seu-site-de-producao.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
def analyze_sentiment(message_list: list[Message]):
    message_texts = [message.message for message in message_list]
    analysis = AnalysisRequest(message_texts)
    return {"analysis": analysis.dict()}
