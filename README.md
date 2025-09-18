# Minimal FastMCP Server (Python)

A tiny MCP server with a single `echo` tool, served over HTTP for Railway.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.server   # http://localhost:8000/health
```

## Tool
```
echo(message: str) → {"message": str, "timestamp": float}
```

## Deploy on Railway (no Docker)
1. Push this repo to GitHub.
2. In Railway: New Project → Deploy from GitHub → select this repo.
3. Wait for build & start (uses railway.toml).
4. Open the service URL and check `/health`.

## Env
- `PORT` (provided by Railway) — defaults to 8000 locally.

## Initialize and push (run these after files are created)
```bash
git init
git add .
git commit -m "chore: minimal FastMCP server with echo tool"
# If gh CLI available:
# gh repo create <REPO_NAME> --public --source=. --remote=origin --push
# Otherwise:
git branch -M main
git remote add origin git@github.com:<you>/<REPO_NAME>.git
git push -u origin main
```
