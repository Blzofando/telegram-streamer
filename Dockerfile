# Usar uma imagem base oficial do Python
FROM python:3.13.0

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Instalar dependências
# Primeiro copiamos só o requirements.txt para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO o resto do seu projeto para o diretório /app
# Isso inclui: main.py, mapeamento_aulas.json e streamer_session.session
COPY . .

# Expor a porta 8000 (que o gunicorn usará)
EXPOSE 8000

# Comando para iniciar o servidor de produção
# Usamos gunicorn para gerenciar workers uvicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]