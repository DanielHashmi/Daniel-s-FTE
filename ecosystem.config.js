module.exports = {
  apps: [
    {
      name: "ai-orchestrator",
      script: "./run-orchestrator.sh",
      interpreter: "bash",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        PYTHONUNBUFFERED: "1",
        DRY_RUN: "false"
      },
      error_file: "AI_Employee_Vault/Logs/orchestrator-error.log",
      out_file: "AI_Employee_Vault/Logs/orchestrator-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      min_uptime: "10s",
      max_restarts: 10,
      restart_delay: 4000
    },
    {
      name: "mcp-email",
      script: "./run-mcp-email.sh",
      interpreter: "bash",
      instances: 1,
      autorestart: true,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1"
      },
      error_file: "AI_Employee_Vault/Logs/mcp-email-error.log",
      out_file: "AI_Employee_Vault/Logs/mcp-email-out.log"
    },
    {
      name: "mcp-social",
      script: "./run-mcp-social.sh",
      interpreter: "bash",
      instances: 1,
      autorestart: true,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1"
      },
      error_file: "AI_Employee_Vault/Logs/mcp-social-error.log",
      out_file: "AI_Employee_Vault/Logs/mcp-social-out.log"
    }
  ]
};
