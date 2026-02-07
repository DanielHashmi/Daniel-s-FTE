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
      name: 'daniel-fte-orchestrator',
      script: 'python',
      args: '-m src.orchestration.orchestrator',
      interpreter: 'python',
      env: {
        PYTHONPATH: '.',
        DRY_RUN: 'true',
        HITL_REQUIRED: 'true',
      },
    },
  ],
};