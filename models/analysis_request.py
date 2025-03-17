from models.message_evaluation import MessageEvaluation
from services import create_juice
import json


class AnalysisRequest:
    process_description: list[str]
    poem: list[str]
    message_list: list[MessageEvaluation]
    
    def __init__(self, message_list):
        self.message_list = [MessageEvaluation(message) for message in message_list]
        self.process_description = []
        self.poem = []
        
        for message in message_list:
            # Prompt para análise de processo - retornando JSON estruturado
            process_prompt = f"""
            Analise o sentimento da mensagem: "{message}"
            
            Forneça uma análise detalhada do processo de análise de sentimentos para esta mensagem.
            
            IMPORTANTE: Retorne APENAS o objeto JSON sem nenhum texto adicional, no seguinte formato:
            
            {{
            "title": "Análise de Sentimentos para: {message}",
            "summary": "Um breve resumo de uma linha sobre a análise geral",
            "steps": [
                {{
                "step_title": "1. Pré-processamento",
                "step_content": "Descrição detalhada desta etapa"
                }},
                {{
                "step_title": "2. Identificação de Palavras-Chave",
                "step_content": "Descrição detalhada desta etapa"
                }},
                {{
                "step_title": "3. Determinação da Polaridade",
                "step_content": "Descrição detalhada desta etapa"
                }},
                {{
                "step_title": "4. Cálculo de Intensidade",
                "step_content": "Descrição detalhada desta etapa"
                }},
                {{
                "step_title": "5. Classificação Final",
                "step_content": "Descrição detalhada desta etapa"
                }}
            ],
            "conclusion": "Uma conclusão sobre o sentimento detectado e sua justificativa"
            }}
            """
            
            # Prompt para poema - retornando JSON estruturado
            poem_prompt = f"""
            Com base na mensagem: "{message}"
            
            Crie um poema expressivo que capture a essência emocional desta mensagem.
            
            IMPORTANTE: Retorne APENAS o objeto JSON sem nenhum texto adicional (como markdown para json, "```json``` ou qualquer marcação), no seguinte formato:
            
            {{
            "title": "Título criativo relacionado à mensagem",
            "style": "Estilo do poema (livre, soneto, haiku, etc)",
            "mood": "Humor predominante do poema (melancólico, alegre, reflexivo, etc)",
            "lines": [
                "primeira linha do poema",
                "segunda linha do poema",
                "terceira linha do poema",
                "e assim por diante..."
            ]
            }}
            
            O poema deve ter entre 8 e 12 linhas, com linguagem poética mas acessível.
            """
            
            # Fazer as chamadas para o Gemini API
            try:
                process_response = create_juice(message, process_prompt)
                self.process_description.append(process_response.text)
            except Exception as e:
                # Fallback em caso de erro
                self.process_description.append(json.dumps({
                    "title": f"Análise de Sentimentos para: {message}",
                    "summary": "Não foi possível processar a análise detalhada",
                    "steps": [{"step_title": "Erro na análise", "step_content": "Ocorreu um erro ao gerar a análise detalhada."}],
                    "conclusion": "Por favor, tente novamente com outra frase."
                }))
                
            try:
                poem_response = create_juice(message, poem_prompt)
                self.poem.append(poem_response.text)
            except Exception as e:
                # Fallback em caso de erro
                self.poem.append(json.dumps({
                    "title": "Reflexão",
                    "style": "Livre",
                    "mood": "Neutro",
                    "lines": ["Não foi possível gerar um poema para esta mensagem."]
                }))
            
    def dict(self):
        return {
            "process_description": self.process_description,
            "poem": self.poem,
            "message_list": [message.dict() for message in self.message_list]
        }
     