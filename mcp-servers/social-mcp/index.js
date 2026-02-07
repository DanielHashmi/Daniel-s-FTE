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
const axios = require('axios'); // For HTTP based APIs (LinkedIn/FB)

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

    this.twitterClient = null;
    this.initClients();
    this.setupToolHandlers();

    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  initClients() {
    // Twitter
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
      console.error('Twitter credentials missing');
    }

    // Instagram - Check for required credentials
    if (process.env.INSTAGRAM_ACCESS_TOKEN && process.env.INSTAGRAM_BUSINESS_ID) {
      console.error('Instagram credentials configured');
    } else {
      console.error('Instagram credentials missing (INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID)');
    }

    // LinkedIn / FB clients are usually initialized per request or via simple token stored in Env
    // We will check for tokens during execution
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
              content: { type: 'string', description: 'Tweet content' }
            },
            required: ['content']
          }
        },
        {
          name: 'post_to_linkedin',
          description: 'Post a text update to LinkedIn',
          inputSchema: {
            type: 'object',
            properties: {
              content: { type: 'string', description: 'Post content' },
              visibility: { type: 'string', enum: ['PUBLIC', 'CONNECTIONS'], default: 'PUBLIC' }
            },
            required: ['content']
          }
        },
        {
          name: 'post_to_facebook',
          description: 'Post update to Facebook Page',
          inputSchema: {
            type: 'object',
            properties: {
              content: { type: 'string', description: 'Post content' },
              page_id: { type: 'string', description: 'Facebook Page ID (optional, uses env if missing)' }
            },
            required: ['content']
          }
        },
        {
          name: 'post_to_instagram',
          description: 'Post image with caption to Instagram Business account',
          inputSchema: {
            type: 'object',
            properties: {
              image_url: { type: 'string', description: 'Public URL of image to post (must be accessible by Instagram)' },
              caption: { type: 'string', description: 'Post caption (max 2200 chars)' },
              hashtags: { type: 'string', description: 'Comma-separated hashtags to append' }
            },
            required: ['image_url', 'caption']
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      // Global Dry Run Check
      if (process.env.DRY_RUN === 'true') {
        return {
          content: [{ type: 'text', text: `[DRY RUN] Would execute ${name} with args: ${JSON.stringify(args)}` }]
        };
      }

      try {
        if (name === 'post_to_twitter') {
          return await this.handlePostTwitter(args.content);
        } else if (name === 'post_to_linkedin') {
          return await this.handlePostLinkedIn(args);
        } else if (name === 'post_to_facebook') {
          return await this.handlePostFacebook(args);
        } else if (name === 'post_to_instagram') {
          return await this.handlePostInstagram(args);
        } else {
          throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{ type: 'text', text: `Error: ${error.message}` }],
          isError: true
        };
      }
    });
  }

  async handlePostTwitter(content) {
    if (!this.twitterClient) throw new Error('Twitter client not initialized');
    const rwClient = this.twitterClient.readWrite;
    const response = await rwClient.v2.tweet(content);
    return {
      content: [{ type: 'text', text: `Posted to Twitter! ID: ${response.data.id}` }]
    };
  }

  async handlePostLinkedIn(args) {
    const token = process.env.LINKEDIN_ACCESS_TOKEN;
    const authorUrn = process.env.LINKEDIN_AUTHOR_URN; // urn:li:person:12345

    if (!token || !authorUrn) throw new Error('Missing LINKEDIN_ACCESS_TOKEN or LINKEDIN_AUTHOR_URN');

    // LinkedIn UGC API
    const response = await axios.post(
      'https://api.linkedin.com/v2/ugcPosts',
      {
        author: authorUrn,
        lifecycleState: 'PUBLISHED',
        specificContent: {
          'com.linkedin.ugc.ShareContent': {
            shareCommentary: { text: args.content },
            shareMediaCategory: 'NONE'
          }
        },
        visibility: {
          'com.linkedin.ugc.MemberNetworkVisibility': args.visibility || 'PUBLIC'
        }
      },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Restli-Protocol-Version': '2.0.0'
        }
      }
    );

    return {
      content: [{ type: 'text', text: `Posted to LinkedIn! ID: ${response.data.id}` }]
    };
  }

  async handlePostFacebook(args) {
    const pageToken = process.env.FACEBOOK_PAGE_TOKEN;
    const pageId = args.page_id || process.env.FACEBOOK_PAGE_ID;

    if (!pageToken || !pageId) throw new Error('Missing FACEBOOK_PAGE_TOKEN or FACEBOOK_PAGE_ID');

    // Facebook Graph API
    const response = await axios.post(
      `https://graph.facebook.com/v19.0/${pageId}/feed`,
      {
        message: args.content,
        access_token: pageToken
      }
    );

    return {
      content: [{ type: 'text', text: `Posted to Facebook! ID: ${response.data.id}` }]
    };
  }

  async handlePostInstagram(args) {
    /**
     * Instagram Content Publishing uses a two-step process:
     * 1. Create a media container with the image URL
     * 2. Publish the container
     * 
     * Requirements:
     * - Instagram Business or Creator account
     * - Facebook Page connected to Instagram
     * - Valid access token with instagram_content_publish permission
     * - Image must be publicly accessible URL
     */
    const accessToken = process.env.INSTAGRAM_ACCESS_TOKEN;
    const instagramAccountId = process.env.INSTAGRAM_BUSINESS_ID;

    if (!accessToken || !instagramAccountId) {
      throw new Error('Missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID');
    }

    // Prepare caption with hashtags
    let fullCaption = args.caption;
    if (args.hashtags) {
      const hashtags = args.hashtags.split(',').map(tag => {
        tag = tag.trim();
        return tag.startsWith('#') ? tag : `#${tag}`;
      }).join(' ');
      fullCaption = `${args.caption}\n\n${hashtags}`;
    }

    // Truncate to Instagram's 2200 character limit
    if (fullCaption.length > 2200) {
      fullCaption = fullCaption.substring(0, 2197) + '...';
    }

    // Step 1: Create media container
    console.error('Creating Instagram media container...');
    const containerResponse = await axios.post(
      `https://graph.facebook.com/v19.0/${instagramAccountId}/media`,
      {
        image_url: args.image_url,
        caption: fullCaption,
        access_token: accessToken
      }
    );

    const containerId = containerResponse.data.id;
    console.error(`Container created: ${containerId}`);

    // Step 2: Wait for container to be ready (Instagram processes the image)
    // Poll the container status before publishing
    let containerReady = false;
    let attempts = 0;
    const maxAttempts = 10;

    while (!containerReady && attempts < maxAttempts) {
      attempts++;
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds

      const statusResponse = await axios.get(
        `https://graph.facebook.com/v19.0/${containerId}`,
        {
          params: {
            fields: 'status_code',
            access_token: accessToken
          }
        }
      );

      const status = statusResponse.data.status_code;
      console.error(`Container status (attempt ${attempts}): ${status}`);

      if (status === 'FINISHED') {
        containerReady = true;
      } else if (status === 'ERROR') {
        throw new Error('Instagram media container processing failed');
      }
    }

    if (!containerReady) {
      throw new Error('Instagram media container not ready after maximum attempts');
    }

    // Step 3: Publish the container
    console.error('Publishing to Instagram...');
    const publishResponse = await axios.post(
      `https://graph.facebook.com/v19.0/${instagramAccountId}/media_publish`,
      {
        creation_id: containerId,
        access_token: accessToken
      }
    );

    const mediaId = publishResponse.data.id;
    console.error(`Published! Media ID: ${mediaId}`);

    return {
      content: [{ type: 'text', text: `Posted to Instagram! Media ID: ${mediaId}` }]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Social MCP server running on stdio');
  }
}

const server = new SocialMcpServer();
server.run().catch(console.error);
