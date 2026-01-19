# Social Media Suite Reference

## Facebook & Instagram Setup (Meta Graph API)

### 1. Create Meta App
1. Go to https://developers.facebook.com/apps
2. Create new app → Business type
3. Add "Facebook Login" and "Instagram Graph API" products
4. Configure OAuth redirect: `http://localhost:8080/callback`

### 2. Get Page Access Token
1. Go to Graph API Explorer
2. Select your app
3. Generate token with permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `instagram_basic`
   - `instagram_content_publish`

### 3. Environment Variables
```bash
export META_ACCESS_TOKEN="your_page_access_token"
export META_PAGE_ID="your_page_id"
export INSTAGRAM_BUSINESS_ID="your_instagram_id"
```

## Twitter/X Setup

### 1. Create Twitter Developer App
1. Go to https://developer.twitter.com/en/portal/projects
2. Create project and app
3. Generate API keys and tokens

### 2. Environment Variables
```bash
export TWITTER_API_KEY="your_api_key"
export TWITTER_API_SECRET="your_api_secret"
export TWITTER_ACCESS_TOKEN="your_access_token"
export TWITTER_ACCESS_SECRET="your_access_secret"
```

## API Rate Limits

### Facebook
- 200 calls/user/hour
- 4800 calls/user/day

### Instagram
- 25 API calls/hour (content publishing)
- 200 reads/hour

### Twitter
- 300 tweets/3 hours (per app)
- 2400 tweets/day (per user)

## Post Formatting Best Practices

### Facebook
- Optimal length: 40-80 characters
- Include call-to-action
- Links auto-expand with preview

### Instagram
- First line is crucial (shows in feed)
- Up to 30 hashtags allowed
- Image required

### Twitter
- Front-load important info
- Use 1-2 hashtags max
- Thread for longer content

## Troubleshooting

### "Invalid access token"
Regenerate token - they expire after 60 days.

### "Media type not supported"
Instagram only: JPG, PNG, GIF (non-animated).

### Rate limit exceeded
Wait for reset or distribute posts over time.
