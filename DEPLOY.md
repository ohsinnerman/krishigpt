# KrishiGPT — Deployment (EC2 backend + Vercel frontend)

Backend (FastAPI + RAG) runs on an **AWS EC2 t3.micro** behind **Caddy** (auto-HTTPS via a
domain). Frontend (Next.js) runs on **Vercel** and calls the backend over HTTPS.

```
Browser ── HTTPS ──> Vercel (Next.js)
   │
   └── HTTPS ──> api.yourdomain.com (Caddy on EC2) ──> 127.0.0.1:8000 (uvicorn)
WhatsApp ── Green-API webhook ──> https://api.yourdomain.com/webhook/greenapi
```

> **The #1 gotcha: RAM.** t3.micro has **1 GB**. PyTorch + the embedding model can exceed
> that. We mitigate with a **3 GB swapfile** and the **CPU-only torch wheel** (~200 MB vs
> ~800 MB). Expect a slow first request while the model loads; steady-state is fine.

---

## Part A — Backend on EC2

### A1. Launch the instance
- AMI: **Ubuntu 22.04 or 24.04 LTS**. Type: **t3.micro**. Disk: **≥ 16 GB** gp3.
- Security group inbound: **22** (SSH, your IP), **80** and **443** (HTTP/HTTPS, 0.0.0.0/0).
  (Do NOT expose 8000 publicly — Caddy fronts it.)
- Create/download the key pair.

### A2. Point DNS at the instance
- Create an **A record** for `api.yourdomain.com` → the instance's **public IPv4**.
  (An Elastic IP is recommended so it survives reboots.)
- Wait for DNS to propagate (`dig api.yourdomain.com` shows the IP) before running Caddy,
  or Let's Encrypt issuance will fail.

### A3. Deploy
```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>

git clone <your-repo-url> /home/ubuntu/krishigpt
cd /home/ubuntu/krishigpt

# Create backend/.env with your keys (copy from .env.example):
cp .env.example backend/.env
nano backend/.env      # set GOOGLE_API_KEY, GOOGLE_API_KEYS, GROQ_API_KEY, GREENAPI_*

# One-shot setup: swap + CPU torch + deps + index + systemd + Caddy
bash deploy/ec2-setup.sh api.yourdomain.com
```
The script builds the FAISS index from the committed seed docs (`scripts/seed_docs.py`), so no
data files need to be transferred.

### A4. Verify
```bash
curl https://api.yourdomain.com/health
# {"status":"ok","chunks_loaded":101,"generator":"gemini-2.5-flash","gemini_configured":true}
journalctl -u krishigpt -f     # live backend logs
```

### A5. Updating later
```bash
cd /home/ubuntu/krishigpt && git pull
# if corpus changed: /home/ubuntu/krishigpt/.venv/bin/python scripts/build_index.py
sudo systemctl restart krishigpt
```

---

## Part B — Frontend on Vercel

1. Push the repo to GitHub.
2. Vercel → **New Project** → import the repo.
3. **Root Directory: `frontend`** (important — the Next.js app is in a subfolder).
   Framework preset auto-detects **Next.js**. Build/output defaults are correct.
4. **Environment Variable:**
   - `NEXT_PUBLIC_API_URL = https://api.yourdomain.com`
   (No trailing slash. This is the only config the frontend needs.)
5. Deploy. Your site is live at `https://<project>.vercel.app`.

> Redeploy after changing the env var (Vercel bakes `NEXT_PUBLIC_*` at build time).

---

## Part C — WhatsApp (Green-API) with the live backend

Now that the backend has a stable HTTPS URL, point Green-API at it (no more ngrok):

- Green-API console → set **Webhook URL** = `https://api.yourdomain.com/webhook/greenapi`
- Ensure **incoming webhook** is enabled and the instance is **authorized**.
- Test: message the bot number from a phone → onboarding flow.

---

## Cost & limits notes
- t3.micro is in the AWS free tier for 12 months (750 h/month). Caddy, swap, Vercel Hobby = free.
- Gemini free tier is 20 req/day/model → the app **auto-falls-over to Groq** (already wired).
  Add more keys to `GOOGLE_API_KEYS` for more headroom.
- Single uvicorn worker only — a second worker would double the model's RAM and OOM the box.

## Troubleshooting
- **Backend OOM / keeps restarting:** confirm swap is on (`free -h` shows Swap 3G) and that you
  installed the **CPU** torch wheel. Check `journalctl -u krishigpt -e`.
- **First request very slow / times out:** the model is loading; the systemd unit warms it at
  startup. Wait for `/health` to return before demoing.
- **Vercel calls fail (mixed content / CORS):** the backend must be **HTTPS** (Caddy). Backend
  CORS is already `*`. Verify `NEXT_PUBLIC_API_URL` is the https domain.
- **Caddy cert fails:** DNS A-record must resolve to the instance and ports 80/443 open before
  first run. `sudo journalctl -u caddy -e`.
