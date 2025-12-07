FROM nginx:alpine

# Copiar configuración de Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar archivos del frontend
COPY app/ /usr/share/nginx/html/

# Script para configuración dinámica
RUN echo '#!/bin/sh' > /docker-entrypoint.d/20-config.sh && \
    echo 'echo "const CONFIG = { API_BASE: process.env.BACKEND_URL || \"http://localhost:8000\" };" > /usr/share/nginx/html/config.js' >> /docker-entrypoint.d/20-config.sh && \
    chmod +x /docker-entrypoint.d/20-config.sh

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]