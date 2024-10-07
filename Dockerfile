# Use uma imagem base do Python
FROM python:3.12-slim

# Defina o diretório de trabalho
WORKDIR /app

# Instala o FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean


# Copie o arquivo requirements.txt para o diretório de trabalho
COPY requirements.txt .

# Cria um ambiente virtual
RUN python -m venv /opt/venv

# Instala as dependências no ambiente virtual
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copie o restante dos arquivos da aplicação
COPY . .

# Comando para executar a aplicação
CMD ["/opt/venv/bin/python", "main.py"]
