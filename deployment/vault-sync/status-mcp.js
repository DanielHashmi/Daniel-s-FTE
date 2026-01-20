#!/usr/bin/env node

/**
 * status-mcp.js - MCP server for vault sync status monitoring
 * Provides sync status, conflict detection, and health checks
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema
} = require('@modelcontextprotocol/sdk/types.js');

// Global state
let syncStatus = {
  lastSync: null,
  agentId: process.env.CLOUD_AGENT_ID || 'cloud-agent-001',
  vaultPath: process.env.VAULT_ROOT || 'AI_Employee_Vault',
  syncLatency: 0,
  pendingActions: 0,
  conflictsDetected: 0
};

/**
 * Detect sync conflicts by checking for duplicate action_ids
 */
function detectConflicts() {
  const fs = require('fs');
  const path = require('path');
  const yaml = require('js-yaml');

  const vaultPath = syncStatus.vaultPath;
  const inProgressPath = path.join(vaultPath, 'In_Progress');
  const conflicts = [];

  try {
    if (!fs.existsSync(inProgressPath)) return [];

    const agents = fs.readdirSync(inProgressPath);
    const actionMap = new Map(); // action_id -> [agent, file]

    agents.forEach(agent => {
      const agentPath = path.join(inProgressPath, agent);
      if (!fs.statSync(agentPath).isDirectory()) return;

      const files = fs.readdirSync(agentPath);
      files.forEach(file => {
        if (!file.endsWith('.yaml')) return;

        const filePath = path.join(agentPath, file);
        try {
          const content = fs.readFileSync(filePath, 'utf8');
          const frontmatter = content.split('---')[1];
          if (frontmatter) {
            const data = yaml.load(frontmatter);
            const actionId = data?.action_id;

            if (actionId) {
              if (actionMap.has(actionId)) {
                conflicts.push({
                  actionId,
                  agents: [actionMap.get(actionId).agent, agent],
                  files: [actionMap.get(actionId).file, file]
                });
              } else {
                actionMap.set(actionId, { agent, file });
              }
            }
          }
        } catch (e) {
          console.error(`Error parsing ${filePath}: ${e.message}`);
        }
      });
    });

    return conflicts;
  } catch (error) {
    console.error('Error detecting conflicts:', error.message);
    return [];
  }
}

/**
 * Get sync status from filesystem timestamps
 */
function getSyncStatus() {
  const fs = require('fs');
  const path = require('path');

  try {
    const vaultPath = syncStatus.vaultPath;
    const syncMarker = path.join(vaultPath, '.sync_timestamp');

    if (fs.existsSync(syncMarker)) {
      const stats = fs.statSync(syncMarker);
      syncStatus.lastSync = stats.mtime.toISOString();
    }

    // Count pending actions
    const needsAction = path.join(vaultPath, 'Needs_Action');
    if (fs.existsSync(needsAction)) {
      const files = fs.readdirSync(needsAction);
      syncStatus.pendingActions = files.filter(f => f.endsWith('.yaml')).length;
    }

    // Check for conflicts
    const conflicts = detectConflicts();
    syncStatus.conflictsDetected = conflicts.length;

    return {
      status: 'healthy',
      lastSync: syncStatus.lastSync,
      pendingActions: syncStatus.pendingActions,
      conflictsDetected: syncStatus.conflictsDetected,
      agentId: syncStatus.agentId,
      syncLatency: syncStatus.syncLatency
    };
  } catch (error) {
    return {
      status: 'error',
      error: error.message,
      lastSync: null,
      pendingActions: 0,
      conflictsDetected: 0
    };
  }
}

/**
 * Check specific agent for claimed actions
 */
function checkAgentStatus(agentId) {
  const fs = require('fs');
  const path = require('path');

  try {
    const vaultPath = syncStatus.vaultPath;
    const agentPath = path.join(vaultPath, 'In_Progress', agentId);

    if (!fs.existsSync(agentPath)) {
      return { agentId, status: 'not_found', claimedCount: 0 };
    }

    const files = fs.readdirSync(agentPath);
    const yamlFiles = files.filter(f => f.endsWith('.yaml'));

    return {
      agentId,
      status: 'active',
      claimedCount: yamlFiles.length,
      path: agentPath
    };
  } catch (error) {
    return {
      agentId,
      status: 'error',
      error: error.message
    };
  }
}

// MCP Server
class SyncMcpServer {
  constructor() {
    this.server = new Server(
      {
        name: 'vault-sync',
        version: '1.0.0'
      },
      {
        capabilities: {
          tools: {}
        }
      }
    );

    this.setupToolHandlers();

    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'get_sync_status',
          description: 'Get overall vault sync status, pending actions, and conflict count',
          inputSchema: {
            type: 'object',
            properties: {}
          }
        },
        {
          name: 'detect_conflicts',
          description: 'Detect and return detailed conflict information for claimed actions',
          inputSchema: {
            type: 'object',
            properties: {}
          }
        },
        {
          name: 'check_agent_status',
          description: 'Check status of a specific agent (cloud or local)',
          inputSchema: {
            type: 'object',
            properties: {
              agentId: {
                type: 'string',
                description: 'Agent identifier (e.g., cloud-agent-001)'
              }
            },
            required: ['agentId']
          }
        }
      ]
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'get_sync_status':
            return {
              content: [{
                type: 'text',
                text: JSON.stringify(getSyncStatus(), null, 2)
              }]
            };

          case 'detect_conflicts':
            return {
              content: [{
                type: 'text',
                text: JSON.stringify({
                  conflicts: detectConflicts(),
                  timestamp: new Date().toISOString()
                }, null, 2)
              }]
            };

          case 'check_agent_status':
            if (!args.agentId) {
              throw new Error('agentId is required');
            }
            return {
              content: [{
                type: 'text',
                text: JSON.stringify(checkAgentStatus(args.agentId), null, 2)
              }]
            };

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{
            type: 'text',
            text: `Error: ${error.message}`
          }],
          isError: true
        };
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Vault Sync MCP server running on stdio');
  }
}

// Run if executed directly
if (require.main === module) {
  const server = new SyncMcpServer();
  server.run().catch(console.error);
}

module.exports = SyncMcpServer;
