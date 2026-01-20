module.exports = {
  apps: [
    {
      name: 'odoo-mcp',
      script: 'deployment/cloud/odoo-mcp.js',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        NODE_ENV: 'production',
        PORT: 8765
      }
    },
    {
      name: 'cloud-email-watcher',
      script: 'src/watchers/cloud_email_watcher.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};
