# KrishiGPT — Deploy without an Elastic IP (Cloudflare Tunnel)

Because there's no Elastic IP, we avoid depending on the EC2 public IP entirely. A
**Cloudflare Tunnel** runs on the instance and connects *outbound* to Cloudflare, giving a
**stable public HTTPS URL** that keeps working even if the instance's IP changes on reboot.
No Elastic IP, no ports 80/443, no cert management.

```
Browser → Vercel (Next.js) ─HTTPS→ <tunnel-url> ─(cloudflared)→ localhost:8000 (uvicorn on EC2)
WhatsApp → Green-API ─HTTPS→ <tunnel-url>/webhook/greenapi
```

There are two flavors of tunnel — pick based on whether you can add a domain to Cloudflare:

| | URL persistence | Needs account | Needs domain |
|---|---|---|---|
| **A. Quick (TryCloudflare)** | changes each restart | ❌ no | ❌ no |
| **B. Named tunnel** | **permanent** | ✅ free | ✅ a domain on Cloudflare |

For a demo you can use **A** (fastest). For a stable URL that won't break your WhatsApp
webhook / Vercel env, use **B**.

---

## Common backend setup (both flavors)

Launch a **t3.micro** Ubuntu instance. Security group inbound: **only port 22 (SSH)** — you do
NOT need 80/443 because the tunnel is outbound. Then:

```bash
ssh -i krishigpt.pem ubuntu@<EC2_PUBLIC_IP>

git clone https://github.com/<you>/krishigpt.git /home/ubuntu/krishigpt
cd /home/ubuntu/krishigpt
cp .env.example backend/.env && nano backend/.env   # add GOOGLE_API_KEY, GROQ_API_KEY, GREENAPI_*

# swap + CPU torch + deps + FAISS index + systemd backend (skips Caddy — pass no domain)
bash deploy/ec2-setup.sh
```
`ec2-setup.sh` with no domain arg sets up swap, deps, the index, and the `krishigpt` systemd
service, then skips the Caddy step. Verify the backend is up locally on the box:
```bash
curl http://127.0.0.1:8000/health      # -> chunks_loaded: 101
```

Install cloudflared:
```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
sudo mv cloudflared /usr/local/bin/cloudflared && sudo chmod +x /usr/local/bin/cloudflared
cloudflared --version
```

---

## Flavor A — Quick TryCloudflare (no account, random URL)

One command gives an instant HTTPS URL:
```bash
cloudflared tunnel --url http://localhost:8000
```
It prints something like:
```
https://random-words-here.trycloudflare.com
```
That URL → your backend. Use it as `NEXT_PUBLIC_API_URL` on Vercel and as the Green-API webhook
base. **Caveat:** it dies when the command stops and the URL changes on restart. To keep it
alive across your SSH session ending, run it under systemd or `nohup`:
```bash
nohup cloudflared tunnel --url http://localhost:8000 > ~/cftunnel.log 2>&1 &
grep -o 'https://[^ ]*trycloudflare.com' ~/cftunnel.log     # read the URL
```
Good enough for a demo. If it restarts, grab the new URL and update Vercel + Green-API.

---

## Flavor B — Named tunnel (free account + a domain, permanent URL)

### B1. Create a free Cloudflare account
1. Go to **https://dash.cloudflare.com/sign-up** → sign up (free).
2. Verify your email.

### B2. Add a domain to Cloudflare (needed for a custom hostname)
- If you own a domain: dash → **Add a site** → enter it → choose the **Free** plan → follow the
  prompt to change your registrar's **nameservers** to the two Cloudflare gives you. Wait until
  the site shows **Active** (can take minutes to a few hours).
- No domain? Get a cheap/free one first (any registrar), then add it as above. A domain is
  required for a *named* tunnel's custom hostname — otherwise use Flavor A.

### B3. Authenticate cloudflared on the instance
```bash
cloudflared tunnel login
```
It prints a URL — open it in your browser, pick your domain, authorize. This drops a cert into
`~/.cloudflared/`.

### B4. Create the named tunnel
```bash
cloudflared tunnel create krishigpt
```
Note the **Tunnel UUID** it prints (and the `~/.cloudflared/<UUID>.json` credentials file).

### B5. Route a hostname to the tunnel
```bash
cloudflared tunnel route dns krishigpt krishigpt-api.<your-cf-domain>
```
This creates the DNS record automatically. Your public URL is now
`https://krishigpt-api.<your-cf-domain>`.

### B6. Config file
```bash
cp /home/ubuntu/krishigpt/deploy/cloudflared-config.example.yml ~/.cloudflared/config.yml
nano ~/.cloudflared/config.yml
# set <TUNNEL_UUID> and <HOSTNAME> = krishigpt-api.<your-cf-domain>
```

### B7. Run it as a service (survives reboots)
```bash
sudo cp /home/ubuntu/krishigpt/deploy/cloudflared.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cloudflared
sudo systemctl status cloudflared --no-pager | head
```

### B8. Verify
```bash
curl https://krishigpt-api.<your-cf-domain>/health
```

---

## Frontend (Vercel) — same for both flavors
1. Push repo to GitHub.
2. Vercel → New Project → import repo → **Root Directory = `frontend`**.
3. Env var: `NEXT_PUBLIC_API_URL = <your tunnel https url>` (no trailing slash).
4. Deploy. Redeploy whenever the tunnel URL changes (Flavor A).

## WhatsApp (Green-API) — same for both
- Green-API console → Webhook URL = `<your tunnel https url>/webhook/greenapi`.
- Update it whenever the Flavor A URL changes.

## Notes
- **Reboots:** with Flavor B (systemd), both `krishigpt` and `cloudflared` come back
  automatically. With Flavor A, re-run the tunnel command and update the URL everywhere.
- **RAM:** the swap + CPU-torch mitigations from `DEPLOY.md` still apply — the tunnel doesn't
  change the 1 GB constraint.
