#!/usr/bin/env node

/**
 * social-mcp - MCP Server for Social Media Operations
 * Handles posting to Twitter/X, LinkedIn, Facebook, Instagram, WhatsApp
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
const { spawn } = require('child_process');

// Load environment variables from project root
dotenv.config({ path: path.join(__dirname, '../../.env') });

const DEFAULT_META_GRAPH_API_VERSION = 'v19.0';
const DEFAULT_WHATSAPP_API_VERSION = 'v19.0';
const WHATSAPP_TO_E164_RE = /^\+?[1-9]\d{6,14}$/;

function extractAxiosError(error) {
  if (!error) return 'Unknown error';
  const responseData = error?.response?.data;
  const responseStatus = error?.response?.status;

  if (responseData && typeof responseData === 'object') {
    const metaError = responseData.error;
    if (metaError && typeof metaError === 'object') {
      const parts = [];
      if (metaError.message) parts.push(String(metaError.message));
      if (metaError.type) parts.push(`type=${metaError.type}`);
      if (metaError.code != null) parts.push(`code=${metaError.code}`);
      if (metaError.error_subcode != null) parts.push(`subcode=${metaError.error_subcode}`);
      if (metaError.fbtrace_id) parts.push(`fbtrace_id=${metaError.fbtrace_id}`);
      if (parts.length > 0) {
        return parts.join(' | ');
      }
    }
    try {
      return JSON.stringify(responseData);
    } catch (jsonError) {
      // ignore stringify failure and keep fallback below
    }
  }

  if (responseStatus) {
    return `HTTP ${responseStatus}`;
  }
  return String(error.message || error);
}

function normalizeHashtagsCsv(rawValue) {
  if (!rawValue) return '';
  const tokens = String(rawValue)
    .split(/[,\s]+/g)
    .map((v) => v.trim())
    .filter(Boolean);
  const out = [];
  const seen = new Set();
  for (const token of tokens) {
    const normalized = token.startsWith('#') ? token : `#${token}`;
    const safe = normalized.replace(/[^\w#]/g, '');
    if (!safe || safe === '#') continue;
    const key = safe.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(safe);
  }
  return out.slice(0, 12).join(' ');
}

function buildCaptionWithHashtags(caption, hashtags) {
  let fullCaption = String(caption || '').trim();
  const normalizedTags = normalizeHashtagsCsv(hashtags);
  if (normalizedTags) {
    fullCaption = fullCaption ? `${fullCaption}\n\n${normalizedTags}` : normalizedTags;
  }
  if (fullCaption.length > 2200) {
    fullCaption = `${fullCaption.substring(0, 2197).trimEnd()}...`;
  }
  return fullCaption;
}

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

  graphApiVersion() {
    const raw = String(process.env.META_GRAPH_API_VERSION || DEFAULT_META_GRAPH_API_VERSION).trim();
    if (!raw) return DEFAULT_META_GRAPH_API_VERSION;
    return raw.startsWith('v') ? raw : `v${raw}`;
  }

  whatsappApiVersion() {
    const raw = String(
      process.env.WHATSAPP_API_VERSION ||
      process.env.META_GRAPH_API_VERSION ||
      DEFAULT_WHATSAPP_API_VERSION
    ).trim();
    if (!raw) return DEFAULT_WHATSAPP_API_VERSION;
    return raw.startsWith('v') ? raw : `v${raw}`;
  }

  graphApiUrl(version, pathSuffix) {
    const safeSuffix = String(pathSuffix || '').replace(/^\/+/, '');
    return `https://graph.facebook.com/${version}/${safeSuffix}`;
  }

  parseBoolean(raw, fallback = false) {
    if (raw == null) return fallback;
    const lowered = String(raw).trim().toLowerCase();
    if (['1', 'true', 'yes', 'on'].includes(lowered)) return true;
    if (['0', 'false', 'no', 'off'].includes(lowered)) return false;
    return fallback;
  }

  isValidHttpUrl(raw) {
    const value = String(raw || '').trim();
    return /^https?:\/\/\S+$/i.test(value);
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

    // Facebook mode/config
    const facebookMethod = (process.env.FACEBOOK_POST_METHOD || 'graph_api').toLowerCase();
    if (facebookMethod === 'playwright') {
      console.error('Facebook configured for Playwright mode');
    } else if (process.env.FACEBOOK_PAGE_TOKEN && process.env.FACEBOOK_PAGE_ID) {
      console.error(`Facebook Graph API credentials configured (${this.graphApiVersion()})`);
    } else {
      console.error('Facebook credentials missing (FACEBOOK_PAGE_TOKEN, FACEBOOK_PAGE_ID)');
    }

    // Instagram mode/config
    const instagramMethod = (process.env.INSTAGRAM_POST_METHOD || 'playwright').toLowerCase();
    if (instagramMethod === 'playwright') {
      console.error('Instagram configured for Playwright mode');
    } else if (process.env.INSTAGRAM_ACCESS_TOKEN && process.env.INSTAGRAM_BUSINESS_ID) {
      console.error(`Instagram Graph API credentials configured (${this.graphApiVersion()})`);
    } else {
      console.error('Instagram credentials missing (INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID)');
    }

    if (process.env.WHATSAPP_ACCESS_TOKEN && process.env.WHATSAPP_PHONE_NUMBER_ID) {
      console.error(`WhatsApp Cloud API credentials configured (${this.whatsappApiVersion()})`);
    } else {
      console.error('WhatsApp credentials missing (WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID)');
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
        },
        {
          name: 'post_to_whatsapp',
          description: 'Send a WhatsApp Cloud API text message',
          inputSchema: {
            type: 'object',
            properties: {
              to: { type: 'string', description: 'Recipient phone number in E.164 format (e.g. +15551234567)' },
              content: { type: 'string', description: 'Message body (max 4096 chars)' },
              preview_url: { type: 'boolean', description: 'Enable URL preview for text messages', default: false }
            },
            required: ['to', 'content']
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name } = request.params;
      const args = request.params.arguments || {};

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
        } else if (name === 'post_to_whatsapp') {
          return await this.handlePostWhatsApp(args);
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
    const method = (process.env.FACEBOOK_POST_METHOD || 'graph_api').toLowerCase();
    if (method === 'playwright') {
      return await this.handlePostFacebookViaPlaywright(args.content);
    }
    if (method !== 'graph_api') {
      throw new Error(`Unsupported FACEBOOK_POST_METHOD: ${method}`);
    }

    const pageToken = process.env.FACEBOOK_PAGE_TOKEN;
    const pageId = args.page_id || process.env.FACEBOOK_PAGE_ID;
    const content = String(args.content || '').trim();

    if (!pageToken || !pageId) throw new Error('Missing FACEBOOK_PAGE_TOKEN or FACEBOOK_PAGE_ID');
    if (!content) throw new Error('Facebook content is required');

    const graphVersion = this.graphApiVersion();
    const payload = new URLSearchParams({
      message: content,
      access_token: pageToken,
    });

    let response;
    try {
      response = await axios.post(
        this.graphApiUrl(graphVersion, `${pageId}/feed`),
        payload.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
    } catch (error) {
      throw new Error(`Facebook Graph API post failed: ${extractAxiosError(error)}`);
    }

    return {
      content: [{ type: 'text', text: `Posted to Facebook via Graph API (${graphVersion})! ID: ${response.data.id}` }]
    };
  }

  async handlePostFacebookViaPlaywright(content) {
    const pythonExe = process.env.PYTHON_EXE || (process.platform === 'win32' ? 'python' : 'python3');
    const scriptPath = path.join(__dirname, '../../src/social/facebook_qwen_poster.py');
    const cwd = path.join(__dirname, '../..');

    return new Promise((resolve, reject) => {
      const proc = spawn(
        pythonExe,
        [scriptPath, '--mode', 'post', '--content', content, '--json'],
        {
          cwd,
          env: { ...process.env },
        }
      );

      let stdout = '';
      let stderr = '';
      proc.stdout.on('data', (chunk) => {
        stdout += chunk.toString();
      });
      proc.stderr.on('data', (chunk) => {
        stderr += chunk.toString();
      });
      proc.on('error', (err) => reject(err));
      proc.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Facebook Playwright post failed: ${stderr || stdout}`));
          return;
        }
        let parsed = null;
        try {
          parsed = JSON.parse(stdout);
        } catch (err) {
          parsed = null;
        }
        const message =
          (parsed && parsed.message) ||
          'Posted to Facebook via Playwright session.';
        resolve({
          content: [{ type: 'text', text: message }],
        });
      });
    });
  }

  async handlePostInstagram(args) {
    const method = (process.env.INSTAGRAM_POST_METHOD || 'playwright').toLowerCase();
    if (method === 'playwright') {
      return await this.handlePostInstagramViaPlaywright(args);
    }
    return await this.handlePostInstagramViaGraphApi(args);
  }

  async handlePostInstagramViaPlaywright(args) {
    const pythonExe = process.env.PYTHON_EXE || (process.platform === 'win32' ? 'python' : 'python3');
    const scriptPath = path.join(__dirname, '../../src/social/instagram_playwright_poster.py');
    const cwd = path.join(__dirname, '../..');

    return new Promise((resolve, reject) => {
      const procArgs = [
        scriptPath,
        '--mode',
        'post',
        '--image-url',
        String(args.image_url || ''),
        '--caption',
        String(args.caption || ''),
        '--json',
      ];
      if (args.hashtags) {
        procArgs.push('--hashtags', String(args.hashtags));
      }

      const proc = spawn(
        pythonExe,
        procArgs,
        {
          cwd,
          env: { ...process.env },
        }
      );

      let stdout = '';
      let stderr = '';
      proc.stdout.on('data', (chunk) => {
        stdout += chunk.toString();
      });
      proc.stderr.on('data', (chunk) => {
        stderr += chunk.toString();
      });
      proc.on('error', (err) => reject(err));
      proc.on('close', (code) => {
        if (code !== 0) {
          let parsedError = '';
          try {
            const parsed = JSON.parse(stdout);
            parsedError = String(parsed?.error || parsed?.message || '').trim();
          } catch (err) {
            parsedError = '';
          }
          const detailParts = [
            parsedError,
            (stderr || '').trim(),
            (stdout || '').trim(),
          ].filter(Boolean);
          reject(new Error(`Instagram Playwright post failed (exit ${code}): ${detailParts.join(' | ')}`));
          return;
        }
        let parsed = null;
        try {
          parsed = JSON.parse(stdout);
        } catch (err) {
          parsed = null;
        }
        const message =
          (parsed && parsed.message) ||
          'Posted to Instagram via Playwright session.';
        resolve({
          content: [{ type: 'text', text: message }],
        });
      });
    });
  }

  async handlePostInstagramViaGraphApi(args) {
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
    const graphVersion = this.graphApiVersion();

    if (!accessToken || !instagramAccountId) {
      throw new Error('Missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID');
    }
    if (!this.isValidHttpUrl(args.image_url)) {
      throw new Error('Instagram image_url must be a valid public http/https URL');
    }
    const caption = String(args.caption || '').trim();
    if (!caption) {
      throw new Error('Instagram caption is required');
    }

    const fullCaption = buildCaptionWithHashtags(caption, args.hashtags);

    // Step 1: Create media container
    console.error('Creating Instagram media container...');
    let containerResponse;
    try {
      const payload = new URLSearchParams({
        image_url: String(args.image_url).trim(),
        caption: fullCaption,
        access_token: accessToken,
      });
      containerResponse = await axios.post(
        this.graphApiUrl(graphVersion, `${instagramAccountId}/media`),
        payload.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
    } catch (error) {
      throw new Error(`Instagram media container create failed: ${extractAxiosError(error)}`);
    }

    const containerId = containerResponse.data.id;
    console.error(`Container created: ${containerId}`);

    // Step 2: Wait for container to be ready (Instagram processes the image)
    // Poll the container status before publishing
    let containerReady = false;
    let attempts = 0;
    const maxAttempts = Number.parseInt(process.env.INSTAGRAM_CONTAINER_MAX_ATTEMPTS || '10', 10) || 10;
    const pollDelayMs = Number.parseInt(process.env.INSTAGRAM_CONTAINER_POLL_MS || '2000', 10) || 2000;

    while (!containerReady && attempts < maxAttempts) {
      attempts++;
      await new Promise(resolve => setTimeout(resolve, pollDelayMs));

      let statusResponse;
      try {
        statusResponse = await axios.get(
          this.graphApiUrl(graphVersion, `${containerId}`),
          {
            params: {
              fields: 'status_code',
              access_token: accessToken,
            },
          }
        );
      } catch (error) {
        throw new Error(`Instagram media status check failed: ${extractAxiosError(error)}`);
      }

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
    let publishResponse;
    try {
      const payload = new URLSearchParams({
        creation_id: containerId,
        access_token: accessToken,
      });
      publishResponse = await axios.post(
        this.graphApiUrl(graphVersion, `${instagramAccountId}/media_publish`),
        payload.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
    } catch (error) {
      throw new Error(`Instagram publish failed: ${extractAxiosError(error)}`);
    }

    const mediaId = publishResponse.data.id;
    console.error(`Published! Media ID: ${mediaId}`);

    return {
      content: [{ type: 'text', text: `Posted to Instagram via Graph API (${graphVersion})! Media ID: ${mediaId}` }]
    };
  }

  async handlePostWhatsApp(args) {
    const accessToken = process.env.WHATSAPP_ACCESS_TOKEN;
    const phoneNumberId = process.env.WHATSAPP_PHONE_NUMBER_ID;
    const apiVersion = this.whatsappApiVersion();
    const to = String(args.to || '').trim();
    const content = String(args.content || '').trim();
    const previewUrl = this.parseBoolean(args.preview_url, false);

    if (!accessToken || !phoneNumberId) {
      throw new Error('Missing WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID');
    }
    if (!WHATSAPP_TO_E164_RE.test(to)) {
      throw new Error('WhatsApp "to" must be in E.164 format (e.g. +15551234567)');
    }
    if (!content) {
      throw new Error('WhatsApp content is required');
    }

    const finalBody = content.length > 4096 ? `${content.slice(0, 4093).trimEnd()}...` : content;
    const endpoint = this.graphApiUrl(apiVersion, `${phoneNumberId}/messages`);

    let response;
    try {
      response = await axios.post(
        endpoint,
        {
          messaging_product: 'whatsapp',
          recipient_type: 'individual',
          to,
          type: 'text',
          text: {
            preview_url: previewUrl,
            body: finalBody,
          },
        },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        }
      );
    } catch (error) {
      throw new Error(`WhatsApp Cloud API send failed: ${extractAxiosError(error)}`);
    }

    const messageId = response?.data?.messages?.[0]?.id || response?.data?.message_id || 'unknown';
    return {
      content: [{ type: 'text', text: `Sent WhatsApp message via Cloud API (${apiVersion}). Message ID: ${messageId}` }]
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
