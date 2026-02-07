#!/usr/bin/env node

/**
 * email-mcp - MCP Server for Email Operations
 * Implements full sending capabilities via Nodemailer and Gmail API
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema
} = require('@modelcontextprotocol/sdk/types.js');
const nodemailer = require('nodemailer');
const { google } = require('googleapis');
const dotenv = require('dotenv');
const path = require('path');
const fs = require('fs');

// Load environment variables from project root
dotenv.config({ path: path.join(__dirname, '../../.env') });

class EmailMcpServer {
  constructor() {
    this.server = new Server(
      {
        name: 'email-mcp',
        version: '1.0.0'
      },
      {
        capabilities: {
          tools: {}
        }
      }
    );

    this.transporter = null;
    this.initTransporter();
    this.setupToolHandlers();

    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  async initTransporter() {
    // Prefer OAuth2 for Gmail if credentials exist, otherwise fallback to SMTP
    try {
      if (process.env.GMAIL_CLIENT_ID && process.env.GMAIL_CLIENT_SECRET && process.env.GMAIL_REFRESH_TOKEN) {
        const OAuth2 = google.auth.OAuth2;
        const oauth2Client = new OAuth2(
          process.env.GMAIL_CLIENT_ID,
          process.env.GMAIL_CLIENT_SECRET,
          "https://developers.google.com/oauthplayground" // Redirect URL
        );

        oauth2Client.setCredentials({
          refresh_token: process.env.GMAIL_REFRESH_TOKEN
        });

        const accessToken = await new Promise((resolve, reject) => {
          oauth2Client.getAccessToken((err, token) => {
            if (err) {
              reject("Failed to create access token: " + err);
            }
            resolve(token);
          });
        });

        this.transporter = nodemailer.createTransport({
          service: "gmail",
          auth: {
            type: "OAuth2",
            user: process.env.EMAIL_USER,
            clientId: process.env.GMAIL_CLIENT_ID,
            clientSecret: process.env.GMAIL_CLIENT_SECRET,
            refreshToken: process.env.GMAIL_REFRESH_TOKEN,
            accessToken: accessToken,
          },
        });
        console.error('Email Transporter initialized (OAuth2)');

      } else if (process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS) {
        // Fallback to standard SMTP
        this.transporter = nodemailer.createTransport({
          host: process.env.SMTP_HOST,
          port: process.env.SMTP_PORT || 587,
          secure: process.env.SMTP_SECURE === 'true',
          auth: {
            user: process.env.SMTP_USER,
            pass: process.env.SMTP_PASS,
          },
        });
        console.error('Email Transporter initialized (SMTP)');
      } else {
        console.error('Email credentials missing. Email capabilities will be limited to DRY RUN.');
      }
    } catch (error) {
      console.error('Failed to initialize transporter:', error);
    }
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'send_email',
          description: 'Send an email (supports attachments)',
          inputSchema: {
            type: 'object',
            properties: {
              to: { type: 'string', description: 'Recipient email address' },
              subject: { type: 'string', description: 'Email subject' },
              text: { type: 'string', description: 'Plain text body' },
              html: { type: 'string', description: 'HTML body (optional)' },
              attachments: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    path: { type: 'string', description: 'Absolute path to file' },
                    filename: { type: 'string', description: 'Name of file attachment' }
                  }
                },
                description: 'List of file attachments'
              }
            },
            required: ['to', 'subject', 'text']
          }
        },
        {
          name: 'verify_connection',
          description: 'Verify email server connection settings',
          inputSchema: {
            type: 'object',
            properties: {}
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (name === 'send_email') {
        return await this.handleSendEmail(args);
      } else if (name === 'verify_connection') {
        return await this.handleVerifyConnection();
      } else {
        throw new Error(`Unknown tool: ${name}`);
      }
    });
  }

  async handleSendEmail(args) {
    // 1. Dry Run Check
    if (process.env.DRY_RUN === 'true' || !this.transporter) {
      return {
        content: [{
          type: 'text',
          text: `[DRY RUN] Would send email to: ${args.to}\nSubject: ${args.subject}\nAttachments: ${args.attachments ? args.attachments.length : 0}`
        }]
      };
    }

    try {
      // 2. Prepare mail options
      const mailOptions = {
        from: process.env.EMAIL_FROM || process.env.EMAIL_USER,
        to: args.to,
        subject: args.subject,
        text: args.text,
        html: args.html,
        attachments: args.attachments ? args.attachments.map(att => ({
            path: att.path,
            filename: att.filename || path.basename(att.path)
        })) : []
      };

      // 3. Send
      const info = await this.transporter.sendMail(mailOptions);
      
      return {
        content: [{
          type: 'text',
          text: `Email sent successfully! Message ID: ${info.messageId}`
        }]
      };
    } catch (error) {
      console.error('Send Error:', error);
      return {
        content: [{ type: 'text', text: `Failed to send email: ${error.message}` }],
        isError: true
      };
    }
  }

  async handleVerifyConnection() {
    if (!this.transporter) {
      return {
        content: [{ type: 'text', text: 'Transporter not initialized (check .env)' }],
        isError: true
      };
    }

    try {
      await this.transporter.verify();
      return {
        content: [{ type: 'text', text: 'Server connection verified and ready.' }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Connection verification failed: ${error.message}` }],
        isError: true
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Email MCP server running on stdio');
  }
}

const server = new EmailMcpServer();
server.run().catch(console.error);