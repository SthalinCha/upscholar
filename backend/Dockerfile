FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Descargar datos de NLTK
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"

# Copiar código
COPY backend/ ./backend/
COPY data/ ./data/

# Crear directorio para embeddings si no existe
RUN mkdir -p data/embeddings

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]