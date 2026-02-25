#!/usr/bin/env node

/**
 * odoo-mcp.js - MCP server for Odoo accounting operations
 * Provides draft/live mode operations and approval workflows
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema
} = require('@modelcontextprotocol/sdk/types.js');
const { spawn } = require('child_process');
const path = require('path');

class OdooMcpServer {
  constructor() {
    this.server = new Server(
      {
        name: 'odoo-mcp',
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
          name: 'get_draft_invoices',
          description: 'Fetch draft invoices from Odoo for review',
          inputSchema: {
            type: 'object',
            properties: {
              limit: {
                type: 'integer',
                description: 'Maximum number of invoices to return',
                default: 50
              },
              mode: {
                type: 'string',
                description: 'Operation mode (draft or live)',
                enum: ['draft', 'live'],
                default: 'draft'
              }
            }
          }
        },
        {
          name: 'validate_invoice',
          description: 'Validate a single invoice before posting',
          inputSchema: {
            type: 'object',
            properties: {
              invoice_id: {
                type: 'integer',
                description: 'Odoo invoice ID'
              },
              mode: {
                type: 'string',
                enum: ['draft', 'live'],
                default: 'draft'
              }
            },
            required: ['invoice_id']
          }
        },
        {
          name: 'validate_invoice_batch',
          description: 'Validate batch of invoices and return detailed report',
          inputSchema: {
            type: 'object',
            properties: {
              invoice_ids: {
                type: 'array',
                items: { type: 'integer' },
                description: 'List of Odoo invoice IDs'
              },
              mode: {
                type: 'string',
                enum: ['draft', 'live'],
                default: 'draft'
              }
            },
            required: ['invoice_ids']
          }
        },
        {
          name: 'post_invoice',
          description: 'Post invoice (requires approval in live mode)',
          inputSchema: {
            type: 'object',
            properties: {
              invoice_id: {
                type: 'integer',
                description: 'Odoo invoice ID'
              },
              mode: {
                type: 'string',
                enum: ['draft', 'live'],
                description: 'Cloud (draft) or local (live) mode'
              },
              require_approval: {
                type: 'boolean',
                description: 'Require approval before posting (live mode)',
                default: true
              }
            },
            required: ['invoice_id', 'mode']
          }
        },
        {
          name: 'post_invoice_batch',
          description: 'Post batch of invoices with approval workflow',
          inputSchema: {
            type: 'object',
            properties: {
              invoice_ids: {
                type: 'array',
                items: { type: 'integer' },
                description: 'List of Odoo invoice IDs'
              },
              mode: {
                type: 'string',
                enum: ['draft', 'live'],
                required: true
              },
              require_approval: {
                type: 'boolean',
                default: true
              }
            },
            required: ['invoice_ids', 'mode']
          }
        },
        {
          name: 'generate_draft_report',
          description: 'Generate CSV report of draft invoices (safe for cloud)',
          inputSchema: {
            type: 'object',
            properties: {
              output_file: {
                type: 'string',
                description: 'Output file path'
              },
              mode: {
                type: 'string',
                enum: ['draft', 'live'],
                default: 'draft'
              }
            }
          }
        },
        {
          name: 'generate_invoice_summary',
          description: 'Generate comprehensive invoice summary with validation',
          inputSchema: {
            type: 'object',
            properties: {
              limit: {
                type: 'integer',
                description: 'Maximum number of invoices',
                default: 100
              },
              mode: {
                type: 'string',
                enum: ['draft', 'live'],
                default: 'draft'
              }
            }
          }
        }
      ]
    }));

    // Handle tool calls by spawning Python script
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      const params = args || {};
      const agentRole = String(process.env.AGENT_ROLE || '').toLowerCase();

      try {
        // Platinum safety: cloud agent is draft-only for accounting posting.
        if (agentRole === 'cloud' && (name === 'post_invoice' || name === 'post_invoice_batch')) {
          return {
            content: [{
              type: 'text',
              text: 'Blocked: cloud role is draft-only for invoice posting. Move approval to local executor.'
            }],
            isError: true
          };
        }

        // Build command
        const cmd = '.claude/skills/odoo-accounting/scripts/main_operation.py';
        let mode = params.mode || 'draft';
        if (agentRole === 'cloud') {
          mode = 'draft';
        }
        let pythonArgs = ['--mode', mode];

        switch (name) {
          case 'get_draft_invoices':
            pythonArgs = [...pythonArgs, 'summary', '--limit', (params.limit || 50).toString()];
            break;

          case 'validate_invoice':
            pythonArgs = [...pythonArgs, 'validate', params.invoice_id.toString()];
            break;

          case 'validate_invoice_batch':
            pythonArgs = [...pythonArgs, 'validate-batch', ...params.invoice_ids.map(id => id.toString())];
            break;

          case 'post_invoice':
            pythonArgs = [...pythonArgs, 'post', params.invoice_id.toString()];
            if (!params.require_approval) {
              pythonArgs.push('--no-approval');
            }
            break;

          case 'post_invoice_batch':
            pythonArgs = [...pythonArgs, 'post-batch', ...params.invoice_ids.map(id => id.toString())];
            if (!params.require_approval) {
              pythonArgs.push('--no-approval');
            }
            break;

          case 'generate_draft_report':
            pythonArgs = [...pythonArgs, 'draft-report'];
            if (params.output_file) {
              pythonArgs.push('--output', params.output_file);
            }
            break;

          case 'generate_invoice_summary':
            pythonArgs = [...pythonArgs, 'summary', '--limit', (params.limit || 100).toString()];
            break;

          default:
            throw new Error(`Unknown tool: ${name}`);
        }

        // Execute Python script
        return new Promise((resolve, reject) => {
          const pythonExe = process.env.PYTHON_EXE || (process.platform === 'win32' ? 'python' : 'python3');
          const pythonProcess = spawn(pythonExe, [cmd, ...pythonArgs], {
            env: { ...process.env }
          });

          let stdout = '';
          let stderr = '';

          pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString();
          });

          pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
          });

          pythonProcess.on('close', (code) => {
            if (code !== 0) {
              resolve({
                content: [{
                  type: 'text',
                  text: `Error executing ${name}: ${stderr}`
                }],
                isError: true
              });
            } else {
              try {
                // Try to parse as JSON
                const result = JSON.parse(stdout);
                resolve({
                  content: [{
                    type: 'text',
                    text: JSON.stringify(result, null, 2)
                  }]
                });
              } catch (e) {
                // Return raw output
                resolve({
                  content: [{
                    type: 'text',
                    text: stdout || stderr
                  }]
                });
              }
            }
          });
        });

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
    console.error('Odoo MCP server running on stdio');
  }
}

if (require.main === module) {
  const server = new OdooMcpServer();
  server.run().catch(console.error);
}

module.exports = OdooMcpServer;
