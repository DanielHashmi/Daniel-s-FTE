const fs = require('fs');
const path = require('path');

function resolvePythonExe() {
  // Resolve a working Python on Windows where `python` may point to a store stub.
  // Preference order: PYTHON_EXE env var -> pythoncore under LOCALAPPDATA -> fallback.
  if (process.env.PYTHON_EXE) return process.env.PYTHON_EXE;

  if (process.platform === 'win32' && process.env.LOCALAPPDATA) {
    const base = path.join(process.env.LOCALAPPDATA, 'Python');
    if (fs.existsSync(base)) {
      const dirs = fs.readdirSync(base).filter((d) => d.startsWith('pythoncore-')).sort();
      for (let i = dirs.length - 1; i >= 0; i--) {
        const candidate = path.join(base, dirs[i], 'python.exe');
        if (fs.existsSync(candidate)) return candidate;
      }
    }
  }

  return process.platform === 'win32' ? 'python' : 'python3';
}

const pythonExe = resolvePythonExe();

module.exports = {
  apps: [
    {
      name: 'daniel-fte-dashboard',
      cwd: './dashboard',
      script: 'npm',
      args: 'run dev',
      env: {
        NODE_ENV: 'development',
        PORT: 3000,
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
    },
    {
      name: 'daniel-fte-orchestrator-local',
      script: pythonExe,
      args: '-m src.orchestration.orchestrator',
      env: {
        PYTHONPATH: '.',
        AGENT_ROLE: 'local',
        AGENT_ID: 'local-agent-001',
        REASONING_ENGINE: 'qwen',
        HITL_REQUIRED: 'true',
      },
    },
    {
      name: 'daniel-fte-orchestrator-cloud',
      script: pythonExe,
      args: '-m src.orchestration.orchestrator',
      env: {
        PYTHONPATH: '.',
        AGENT_ROLE: 'cloud',
        AGENT_ID: 'cloud-agent-001',
        REASONING_ENGINE: 'qwen',
        HITL_REQUIRED: 'true',
        // Cloud is draft-only; force dry-run safety even if someone misconfigures MCP creds.
        DEV_MODE: 'true',
      },
    },
  ],
};
