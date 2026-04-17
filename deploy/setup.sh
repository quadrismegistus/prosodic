#!/bin/bash
set -euo pipefail

# Server setup script for prosodic.app on a Debian/Ubuntu VPS.
# Assumes nginx + certbot are installable (or already present for a co-hosted box).
# Run as root or with sudo.
#
# Prerequisites: point prosodic.app and www.prosodic.app DNS A records to this server.
#
# Usage:
#   scp -r deploy/ root@YOUR_SERVER_IP:/tmp/prosodic-deploy
#   ssh root@YOUR_SERVER_IP bash /tmp/prosodic-deploy/setup.sh

DEPLOY_DIR=/tmp/prosodic-deploy
DOMAIN=prosodic.app
EMAIL="${CERTBOT_EMAIL:-admin@${DOMAIN}}"

echo "=== Prosodic server setup ==="

# --- System packages ---
apt-get update
apt-get install -y python3 python3-venv python3-pip espeak git nginx certbot python3-certbot-nginx curl

# --- Node.js (for frontend build) ---
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

# --- Create user ---
if ! id prosodic &>/dev/null; then
    useradd -r -m -d /opt/prosodic -s /bin/bash prosodic
    echo "Created user 'prosodic'"
fi

# --- Clone/update repo ---
REPO=/opt/prosodic/repo
if [ -d "$REPO/.git" ]; then
    cd "$REPO" && sudo -u prosodic git pull
else
    sudo -u prosodic git clone https://github.com/quadrismegistus/prosodic.git "$REPO"
fi

# --- Python venv ---
VENV=/opt/prosodic/.venv
if [ ! -d "$VENV" ]; then
    sudo -u prosodic python3 -m venv "$VENV"
fi
cd /opt/prosodic
sudo -Hu prosodic "$VENV/bin/pip" install --upgrade pip
sudo -Hu prosodic "$VENV/bin/pip" install -e "$REPO"

# --- Build frontend ---
cd "$REPO/prosodic/web/frontend"
sudo -u prosodic npm install
sudo -u prosodic npm run build

# --- Install systemd service ---
cp "$DEPLOY_DIR/prosodic.service" /etc/systemd/system/
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$REPO|" /etc/systemd/system/prosodic.service
sed -i "s|ExecStart=.*|ExecStart=$VENV/bin/python -m uvicorn prosodic.web.api:app --host 127.0.0.1 --port 8181|" /etc/systemd/system/prosodic.service
systemctl daemon-reload
systemctl enable --now prosodic
echo "Prosodic service started on 127.0.0.1:8181"

# --- Install nginx site ---
cp "$DEPLOY_DIR/nginx-prosodic.conf" /etc/nginx/sites-available/prosodic
ln -sf /etc/nginx/sites-available/prosodic /etc/nginx/sites-enabled/prosodic
nginx -t
systemctl reload nginx
echo "Nginx vhost installed (HTTP only — certbot will add TLS next)"

# --- TLS via certbot ---
certbot --nginx \
    -d "$DOMAIN" -d "www.$DOMAIN" \
    --non-interactive --agree-tos -m "$EMAIL" \
    --redirect

systemctl reload nginx
echo "TLS provisioned — auto-renewal via certbot.timer"

echo ""
echo "=== Done ==="
echo "Visit https://$DOMAIN"
echo ""
echo "Useful commands:"
echo "  journalctl -u prosodic -f          # app logs"
echo "  journalctl -u nginx -f             # nginx logs"
echo "  systemctl restart prosodic         # restart app"
echo "  certbot renew --dry-run            # test cert renewal"
echo "  sudo -u prosodic $VENV/bin/python -c 'import prosodic; print(prosodic.__version__)'"
