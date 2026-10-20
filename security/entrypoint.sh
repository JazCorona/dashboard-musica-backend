#!/bin/bash
set -e
mkdir -p /var/log/nginx /var/run/fail2ban /run
# Fail2Ban necesita un archivo de log real y legible.
touch /var/log/nginx/access.log /var/log/nginx/error.log /var/log/fail2ban.log
rm -f /var/run/fail2ban/fail2ban.sock /var/run/fail2ban/fail2ban.pid

# 1) App (uvicorn) SOLO en loopback: nadie la alcanza sin pasar por nginx.
uvicorn app.main:app --host 127.0.0.1 --port 9001 &

# 2) Nginx al frente en el puerto público 8001.
nginx -g 'daemon off;' &

# 3) Fail2Ban vigilando el access.log de nginx.
sleep 1
fail2ban-client -x start

echo "[backend-protected] uvicorn(127.0.0.1:9001) + nginx(:8001) + fail2ban ACTIVOS"
exec tail -F /var/log/fail2ban.log
