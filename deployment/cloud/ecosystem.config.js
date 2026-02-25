const fs = require('fs');
const path = require('path');

function resolvePythonExe() {
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
    return 'python';
  }
  return 'python3';
}

const projectRoot = path.resolve(__dirname, '..', '..');
const pythonExe = resolvePythonExe();

module.exports = {
  apps: [
    {
      name: 'daniel-fte-orchestrator-cloud',
      cwd: projectRoot,
      script: pythonExe,
      args: '-m src.orchestration.orchestrator',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        PYTHONPATH: '.',
        PYTHONUNBUFFERED: '1',
        AGENT_ROLE: 'cloud',
        AGENT_ID: process.env.CLOUD_AGENT_ID || 'cloud-agent-001',
        REASONING_ENGINE: process.env.REASONING_ENGINE || 'qwen',
        HITL_REQUIRED: 'true',
        DEV_MODE: process.env.DEV_MODE || 'true',
      },
    },
    {
      name: 'daniel-fte-odoo-mcp',
      cwd: projectRoot,
      script: 'node',
      args: 'deployment/cloud/odoo-mcp.js',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      env: {
        NODE_ENV: 'production',
      },
    },
  ],
};
