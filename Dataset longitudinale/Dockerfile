FROM python:3.12-slim

# Imposta la cartella di lavoro come /app (dove il volume viene montato)
WORKDIR /app

# Copia i file necessari per l'installazione delle dipendenze
COPY requirements.txt .


# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt




