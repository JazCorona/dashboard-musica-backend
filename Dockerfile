FROM python:3.11-slim

WORKDIR /app

# --- Dependencias de la app ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

# --- Capa de seguridad: Nginx (reverse proxy) + Fail2Ban (anti HTTP-flood) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
      nginx fail2ban iptables procps \
    && rm -rf /var/lib/apt/lists/*

COPY security/nginx.conf             /etc/nginx/nginx.conf
COPY security/jail.local             /etc/fail2ban/jail.local
COPY security/filter-http-flood.conf /etc/fail2ban/filter.d/http-flood.conf
COPY security/entrypoint.sh          /entrypoint.sh
RUN chmod +x /entrypoint.sh

# El puerto público lo sirve Nginx (uvicorn queda en 127.0.0.1:9001).
EXPOSE 8001
ENTRYPOINT ["/entrypoint.sh"]
