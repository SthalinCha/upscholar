FROM nginx:alpine

# Copiar configuración simplificada
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar frontend
COPY app/ /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
