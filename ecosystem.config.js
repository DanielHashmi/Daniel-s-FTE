module.exports = {
  apps: [
    {
      name: 'ai-watcher-filesystem',
      script: 'src/watchers/filesystem_watcher.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '50M',
      env: {
        PYTHONUNBUFFERED: '1',
        WATCHER_TYPE: 'filesystem'
      },
      error_file: 'AI_Employee_Vault/Logs/pm2-error.log',
      out_file: 'AI_Employee_Vault/Logs/pm2-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000
    },
    {
      name: 'ai-watcher-gmail',
      script: 'src/watchers/gmail_watcher.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '50M',
      env: {
        PYTHONUNBUFFERED: '1',
        WATCHER_TYPE: 'gmail'
      },
      error_file: 'AI_Employee_Vault/Logs/pm2-error.log',
      out_file: 'AI_Employee_Vault/Logs/pm2-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000
    }
  ]
};
