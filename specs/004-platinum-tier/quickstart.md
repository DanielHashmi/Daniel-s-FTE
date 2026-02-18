# Platinum Tier Quickstart (Cloud + Local)

This quickstart follows the Hackathon 0 Platinum split:
- Cloud drafts
- Local approves and executes

## 1) Prerequisites

- Node.js 20+
- Python 3.12+
- Qwen CLI (`qwen` / `qwen.cmd`)
- Playwright Chromium (for browser-session flows)

## 2) Install Dependencies

```powershell
cd "C:\Users\kk\Desktop\Daniel's FTE"
python -m pip install -e .
python -m playwright install chromium
cd dashboard
npm install
```

## 3) Configure `.env`

Start from `.env.example` and set at least:

```bash
DRY_RUN=true
REASONING_ENGINE=qwen
AGENT_ROLE=local
AGENT_ID=local-agent-001
STRICT_WORK_ZONES=true
```

## 4) Start Local Surfaces

```powershell
START_DASHBOARD.bat
START_BRAIN_LOCAL.bat
```

## 5) Start Cloud Drafter (dev host or VM)

```powershell
START_BRAIN_CLOUD.bat
```

## 6) Run Platinum Gate

```powershell
RUN_PLATINUM_DEMO_GATE.bat
```

Expected: cloud draft -> local approve -> MCP execute -> logs -> `Done/`.

## 7) Optional Cloud Odoo Deployment

Use:
- `deployment/cloud/README.md`
- `deployment/cloud/docker-compose.odoo.yml`
