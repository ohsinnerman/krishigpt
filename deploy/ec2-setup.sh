#!/usr/bin/env bash
#
# KrishiGPT — one-shot EC2 (Ubuntu 22.04/24.04, t3.micro) bootstrap.
# Run as the 'ubuntu' user after cloning the repo to /home/ubuntu/krishigpt.
#
#   git clone <your-repo> /home/ubuntu/krishigpt
#   cd /home/ubuntu/krishigpt
#   # create backend/.env with your keys (see .env.example)
#   bash deploy/ec2-setup.sh api.yourdomain.com
#
set -euo pipefail

DOMAIN="${1:-}"
REPO="/home/ubuntu/krishigpt"
BACKEND="$REPO/backend"
VENV="$REPO/.venv"

echo "==> [0/8] Disk space preflight"
AVAIL_GB=$(df --output=avail -BG / | tail -1 | tr -dc '0-9')
echo "Free space on / : ${AVAIL_GB} GB"
if [ "${AVAIL_GB:-0}" -lt 6 ]; then
  echo "!! Less than 6 GB free on /. Grow the EBS volume to >=15 GB, then:"
  echo "!!   lsblk ; sudo growpart /dev/nvme0n1 1 ; sudo resize2fs /dev/nvme0n1p1"
  echo "!! (device may be /dev/xvda instead). Then re-run this script."
  exit 1
fi
# NOTE: pip temp/cache are redirected to the real disk in step [3] because /tmp
# is a small RAM-backed tmpfs that overflows when unpacking the torch wheel.

echo "==> [1/8] Swap (critical: t3.micro has only 1 GB RAM)"
if [ ! -f /swapfile ]; then
  sudo fallocate -l 3G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=3072
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  # be swap-friendly
  echo 'vm.swappiness=60' | sudo tee /etc/sysctl.d/99-swap.conf
  sudo sysctl -p /etc/sysctl.d/99-swap.conf
fi
free -h

echo "==> [2/8] System packages"
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip build-essential debian-keyring debian-archive-keyring apt-transport-https curl

echo "==> [3/8] Python venv + CPU-only torch + deps"
# /tmp is a small RAM-backed tmpfs (~half of RAM). Unpacking the ~192MB torch
# wheel there overflows it -> "[Errno 122] Disk quota exceeded". Redirect pip's
# temp + cache to the real disk instead.
export TMPDIR="$REPO/.pip-tmp"
export PIP_CACHE_DIR="$REPO/.pip-cache"
mkdir -p "$TMPDIR" "$PIP_CACHE_DIR"

python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
# CPU-only torch wheel (~200MB vs ~800MB CUDA) — essential on 1 GB RAM.
"$VENV/bin/pip" install --index-url https://download.pytorch.org/whl/cpu torch
"$VENV/bin/pip" install -r "$BACKEND/requirements-cpu.txt"
# Reclaim the download cache space once installed.
rm -rf "$TMPDIR" "$PIP_CACHE_DIR"

echo "==> [4/8] Build corpus + FAISS index"
"$VENV/bin/python" "$REPO/scripts/download_corpus.py"
"$VENV/bin/python" "$REPO/scripts/build_index.py"

echo "==> [5/8] Sanity: .env present?"
if [ ! -f "$BACKEND/.env" ]; then
  echo "!! $BACKEND/.env is missing. Copy .env.example and add GOOGLE_API_KEY / GROQ_API_KEY."
  exit 1
fi

echo "==> [6/8] systemd service"
sudo cp "$REPO/deploy/krishigpt.service" /etc/systemd/system/krishigpt.service
sudo systemctl daemon-reload
sudo systemctl enable krishigpt
sudo systemctl restart krishigpt
sleep 8
sudo systemctl --no-pager status krishigpt | head -20 || true
curl -s http://127.0.0.1:8000/health || echo "(health not ready yet — check: journalctl -u krishigpt -f)"

echo "==> [7/8] Public HTTPS"
if [ -n "$DOMAIN" ]; then
  # Domain provided -> Caddy auto-HTTPS reverse proxy (needs ports 80/443 open + DNS -> this IP).
  if ! command -v caddy >/dev/null 2>&1; then
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
    sudo apt-get update -y && sudo apt-get install -y caddy
  fi
  sudo sed "s/api.yourdomain.com/$DOMAIN/" "$REPO/deploy/Caddyfile" | sudo tee /etc/caddy/Caddyfile >/dev/null
  sudo systemctl restart caddy
  echo "Caddy serving https://$DOMAIN -> 127.0.0.1:8000"
else
  echo "No domain passed -> Caddy skipped."
  echo "Use a Cloudflare Tunnel for a public HTTPS URL (no Elastic IP / domain needed):"
  echo "  see deploy/DEPLOY-cloudflare.md"
fi

echo "==> [8/8] Done."
echo "Backend health (local):  curl http://127.0.0.1:8000/health"
echo "Backend logs:            journalctl -u krishigpt -f"
