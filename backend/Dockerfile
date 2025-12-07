FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Descargar datos de NLTK
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"

# Crear directorio para datos
RUN mkdir -p data

# Copiar código fuente y datos
COPY app/ ./app/
COPY data/documentos.csv ./data/

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
