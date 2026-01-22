module.exports = {
  apps: [{
    name: 'ai-orchestrator',
    script: 'src/orchestration/orchestrator.py',
    interpreter: './venv/bin/python',
    cwd: process.cwd(),
    env: { PYTHONPATH: '.' },
    error_file: './AI_Employee_Vault/Logs/orchestrator-err.log',
    out_file: './AI_Employee_Vault/Logs/orchestrator-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm Z'
  }, {
    name: 'mcp-email',
    script: './mcp-servers/email-mcp/index.js'
  }, {
    name: 'mcp-social',
    script: './mcp-servers/social-mcp/index.js'
  }, {
    name: 'mcp-odoo',
    script: './deployment/cloud/odoo-mcp.js'
  }]
};