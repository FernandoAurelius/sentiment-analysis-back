# API de Análise de Sentimentos

API para análise de sentimentos usando FastAPI, Google Gemini e NLPCloud.

## Execução Local

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

2. Configure as variáveis de ambiente no arquivo `.env`.

3. Execute o servidor:
   ```
   uvicorn main:app --reload
   ```
   
   Ou use o script start.sh (no Linux/Mac):
   ```
   chmod +x start.sh
   ./start.sh
   ```

## Deploy no Railway

1. Faça login no Railway:
   ```
   railway login
   ```

2. Inicialize o projeto:
   ```
   railway init
   ```

3. Realize o deploy:
   ```
   railway up
   ```

Alternativamente, você pode conectar seu repositório GitHub ao Railway para deploy automático.

## Variáveis de Ambiente

Configure as seguintes variáveis de ambiente no Railway:

- `GEMINI_API_KEY` - Chave API do Google Gemini
- `NLPCLOUD_API_KEY` - Chave API do NLPCloud
- `GEMINI_MAX_REQUESTS_PER_MINUTE` - Limite de requisições por minuto (padrão: 60)
- `GEMINI_MAX_RETRIES` - Máximo de tentativas em caso de falha (padrão: 3)
- `GEMINI_RETRY_DELAY_BASE` - Tempo base para backoff exponencial (padrão: 2.0)

## Endpoints

- `GET /health` - Verifica se a API está operacional
- `POST /analyze` - Analisa o sentimento de uma ou mais mensagens
- `POST /debug` - Endpoint para debugging que mostra o que foi recebido

## Estrutura do Projeto

- `main.py` - Ponto de entrada da aplicação
- `models/` - Modelos de dados
- `services.py` - Serviços para APIs externas
- `railway.json` - Configuração para deploy no Railway
