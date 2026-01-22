#!/usr/bin/env node

/**
 * social-mcp - MCP Server for Social Media Operations
 * Handles posting to Twitter/X, LinkedIn, Facebook, Instagram
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema
} = require('@modelcontextprotocol/sdk/types.js');
const { TwitterApi } = require('twitter-api-v2');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables from project root
dotenv.config({ path: path.join(__dirname, '../../.env') });

class SocialMcpServer {
  constructor() {
    this.server = new Server(
      {
        name: 'social-mcp',
        version: '1.0.0'
      },
      {
        capabilities: {
          tools: {}
        }
      }
    );

    // Initialize Twitter Client
    this.twitterClient = null;
    this.initTwitterClient();

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  initTwitterClient() {
    // Check for required Twitter credentials
    const appKey = process.env.TWITTER_API_KEY;
    const appSecret = process.env.TWITTER_API_SECRET;
    const accessToken = process.env.TWITTER_ACCESS_TOKEN;
    const accessSecret = process.env.TWITTER_ACCESS_TOKEN_SECRET;

    if (appKey && appSecret && accessToken && accessSecret) {
      this.twitterClient = new TwitterApi({
        appKey,
        appSecret,
        accessToken,
        accessSecret,
      });
      console.error('Twitter client initialized');
    } else {
      console.error('Twitter credentials missing - Twitter functionality disabled');
    }
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'post_to_twitter',
          description: 'Post a tweet to Twitter/X',
          inputSchema: {
            type: 'object',
            properties: {
              content: {
                type: 'string',
                description: 'The text content of the tweet (max 280 chars)'
              }
            },
            required: ['content']
          }
        },
        {
            name: 'verify_twitter_credentials',
            description: 'Verify if Twitter credentials are valid and working',
            inputSchema: {
                type: 'object',
                properties: {}
            }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        if (name === 'post_to_twitter') {
            return await this.handlePostTwitter(args.content);
        } else if (name === 'verify_twitter_credentials') {
            return await this.handleVerifyTwitter();
        } else {
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

  async handlePostTwitter(content) {
    if (!this.twitterClient) {
        throw new Error('Twitter client not initialized. Check .env credentials.');
    }

    // Check for DRY_RUN mode
    if (process.env.DRY_RUN === 'true') {
        return {
            content: [{
                type: 'text',
                text: `[DRY RUN] Would have posted to Twitter: "${content}"`
            }]
        };
    }

    try {
        const rwClient = this.twitterClient.readWrite;
        const response = await rwClient.v2.tweet(content);
        
        return {
            content: [{
                type: 'text',
                text: `Successfully posted to Twitter! ID: ${response.data.id}\nText: ${response.data.text}`
            }]
        };
    } catch (error) {
        console.error('Twitter API Error:', error);
        throw new Error(`Failed to post to Twitter: ${error.message}`);
    }
  }

  async handleVerifyTwitter() {
      if (!this.twitterClient) {
          throw new Error('Twitter client not initialized. Missing credentials.');
      }
      
      try {
          const user = await this.twitterClient.currentUser();
          return {
              content: [{
                  type: 'text',
                  text: `Twitter Credentials Valid! Connected as: @${user.screen_name} (ID: ${user.id_str})`
              }]
          };
      } catch (error) {
          throw new Error(`Twitter verification failed: ${error.message}`);
      }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Social MCP server running on stdio');
  }
}

const server = new SocialMcpServer();
server.run().catch(console.error);