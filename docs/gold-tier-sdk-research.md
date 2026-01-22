# Gold Tier Python SDK Research Report

**Date:** 2026-01-19
**Purpose:** Research Python SDKs and API clients for Gold Tier implementation (Xero, Facebook, Instagram, Twitter)

---

## 1. Xero SDK

### Package Information
- **Official Package:** `xero-python`
- **Installation:** `pip install xero-python`
- **Python Support:** Python >= 3.5
- **Repository:** https://github.com/XeroAPI/xero-python
- **Documentation:** https://xeroapi.github.io/xero-python/

### Authentication Pattern

**OAuth 2.0 Flow:**
```python
from xero_python.api_client import ApiClient
from xero_python.accounting import AccountingApi

# Token persistence pattern
@api_client.oauth2_token_getter
def obtain_xero_oauth2_token():
    return session.get("token")

@api_client.oauth2_token_saver
def store_xero_oauth2_token(token):
    session["token"] = token
```

**Token Details:**
- Access token: 30-minute expiration (1800 seconds)
- Refresh token: 60-day validity
- Must refresh access token prior to making API calls
- Store token set JSON in datastore in relation to authenticated user

**Custom Connections (M2M):**
- Premium Xero option for machine-to-machine integrations
- Uses `client_credentials` grant type
- Eliminates user authorization flow
- `xeroTenantId` can be an empty string

### Key Capabilities

**API Sets Available:**
- **Accounting API:** Main Xero application functions (most commonly used)
  - Invoices, contacts, payments, transactions
- **Assets API:** Fixed asset management
- **Files API:** File and folder management
- **Projects API:** Time and cost tracking
- **Payroll APIs:** Available for AU, UK, and NZ regions
- **App Store Subscriptions:** Marketplace billing integration

**Reading Invoices:**
```python
accounting_api = AccountingApi(api_client)
invoices_read = accounting_api.get_invoices(xero_tenant_id)
```

**Creating Invoices:**

Required Invoice Fields:
- `type`: Invoice type - `"ACCPAY"`, `"ACCREC"`, `"ACCPAYCREDIT"`, `"ACCRECCREDIT"`
- `contact`: Contact object
- `line_items`: List of LineItem objects

Key Optional Fields:
- `date`: Invoice date (YYYY-MM-DD format)
- `due_date`: Due date (YYYY-MM-DD format)
- `invoice_number`: Unique identifier (max 255 characters)
- `reference`: Additional reference number
- `status`: `"DRAFT"`, `"SUBMITTED"`, `"AUTHORISED"`, `"PAID"`, `"VOIDED"`
- `currency_code`: CurrencyCode enum

Financial Fields (read-only):
- `sub_total`: Total excluding taxes
- `total_tax`: Total tax amount
- `total`: Tax-inclusive total
- `amount_due`: Remaining balance
- `amount_paid`: Sum of payments received

**Error Handling:**
```python
from xero_python.exceptions import AccountingBadRequestException

try:
    invoices_read = accounting_api.get_invoices(xero_tenant_id)
except AccountingBadRequestException as exception:
    output = "Error: " + exception.reason
```

### Rate Limits

**Status:** Unable to access official documentation (authorization required)

**Best Practices:**
- Implement token refresh before API calls
- Validate state parameter in OAuth callback (CSRF protection)
- Wrap API calls in try-except blocks with specific exception types
- SDK is auto-generated from Xero's OpenAPI specifications

### Important Notes
- SDK supports multiple API sets beyond accounting
- Custom Connections are a premium option for single-organization integrations
- Token management is critical - access tokens expire quickly
- Sample applications available:
  - Starter app: https://github.com/XeroAPI/xero-python-oauth2-starter
  - Full app: https://github.com/XeroAPI/xero-python-oauth2-app

---

## 2. Facebook SDK

### Package Information

**Option 1: facebook-sdk (NOT RECOMMENDED)**
- **Package:** `facebook-sdk`
- **Installation:** `pip install facebook-sdk`
- **Status:** OUTDATED - Last release November 2018
- **Python Support:** Python 2.7, 3.4-3.7 (outdated versions)
- **Repository:** https://github.com/mobolic/facebook-sdk

**Option 2: facebook-python-business-sdk (RECOMMENDED FOR BUSINESS/ADS)**
- **Package:** `facebook_business`
- **Installation:** `pip install facebook_business`
- **Status:** Actively maintained by Meta
- **Repository:** https://github.com/facebook/facebook-python-business-sdk
- **Focus:** Marketing APIs, Business Manager, Pages, Instagram

**Option 3: python-facebook (RECOMMENDED FOR GENERAL USE)**
- **Package:** `python-facebook-api`
- **Installation:** `pip install --upgrade python-facebook-api`
- **Python Support:** Python 3.6+
- **Repository:** https://github.com/sns-sdks/python-facebook
- **Documentation:** https://sns-sdks.lkhardy.cn/python-facebook/

### Authentication Pattern

**python-facebook Library:**

Three initialization methods:

1. **Direct Token:**
```python
from pyfacebook import GraphAPI

api = GraphAPI(access_token="your_token")
```

2. **App-Only Auth:**
```python
api = GraphAPI(
    app_id="your_app_id",
    app_secret="your_app_secret",
    application_only_auth=True
)
```

3. **OAuth Flow:**
```python
api = GraphAPI(
    app_id="your_app_id",
    app_secret="your_app_secret",
    oauth_flow=True
)

# Get authorization URL
auth_url = api.get_authorization_url()

# After user authenticates
access_token = api.exchange_user_access_token(response_url)
```

**facebook-python-business-sdk:**
```python
from facebook_business.api import FacebookAdsApi

FacebookAdsApi.init(app_id, app_secret, access_token)
```

### Key Capabilities

**python-facebook API Methods:**
- `get_object(object_id)` - Retrieve single object data
- `get_objects(ids)` - Retrieve multiple objects at once
- `get_connection(object_id, connection)` - Get edge data (e.g., posts from page)
- `get_full_connections()` - Same as above with automatic pagination
- `post_object(object_id, connection, data)` - Create/publish data
- `delete_object(object_id)` - Delete data

**Creating Posts Example:**
```python
# Post a comment
response = api.post_object(
    object_id="page_id_post_id",
    connection="comments",
    data={"message": "Comment by the api"}
)
```

**Supported APIs:**
- Facebook Graph API (Application, Page, User, Group, Event edges)
- Instagram Business Graph API
- Instagram Basic Display API

### Rate Limits

**Status:** Rate limiting applies but specific numbers not documented in SDK

**Best Practices:**
- Each API call counts individually towards rate limiting
- Batch calls have optimal numbers per batch
- Monitor response headers for rate limit information

### Important Notes
- For page posting, requires Page Access Token with `manage_page` permission
- facebook-sdk is outdated and should be avoided
- facebook-python-business-sdk focuses on advertising/marketing
- python-facebook is most versatile for general Graph API usage
- Graph Explorer tool useful for obtaining tokens during development

---

## 3. Instagram SDK

### Package Information

**Status:** No official standalone Python SDK from Meta

**Approach:** Use Facebook Graph API via one of these methods:

1. **python-facebook library** (recommended)
   - Package: `python-facebook-api`
   - Installation: `pip install --upgrade python-facebook-api`
   - Supports Instagram Business Graph API

2. **Direct HTTP requests** using `requests` library
   - More control but requires manual implementation
   - Must handle authentication and API calls directly

3. **instagram_simple_post** (community library)
   - Repository: https://github.com/remc0r/instagram_simple_post
   - Simplified interface for posting
   - Requires Filestack for media storage

### Authentication Requirements

**Prerequisites:**
- Instagram Business or Creator account
- Facebook Page connected to Instagram account
- Facebook App with Instagram permissions
- Access token with appropriate scopes

**Authentication Pattern:**
Same as Facebook Graph API (see Facebook SDK section above)

### Posting Capabilities

**Instagram Content Publishing API Workflow:**

Instagram uses a two-step process:

1. **Create Media Container:**
   - Upload image/video to accessible URL
   - Create container with media URL and caption
   - Returns container ID

2. **Publish Container:**
   - Use container ID to publish post
   - Post appears on Instagram profile

**Simplified Example (instagram_simple_post):**
```python
import instagram_simple_post

# Configuration required: Access Token, User ID, Filestack API Key
instagram_simple_post.publish_image(
    '<PATH_TO_IMAGE>',
    'Description of my post'
)
```

**Manual Implementation Pattern:**
```python
import requests

# Step 1: Create container
container_response = requests.post(
    f"https://graph.facebook.com/v18.0/{instagram_user_id}/media",
    params={
        "image_url": "https://example.com/image.jpg",
        "caption": "My post caption #hashtags",
        "access_token": access_token
    }
)
container_id = container_response.json()["id"]

# Step 2: Publish container
publish_response = requests.post(
    f"https://graph.facebook.com/v18.0/{instagram_user_id}/media_publish",
    params={
        "creation_id": container_id,
        "access_token": access_token
    }
)
```

### Posting Features

**Supported Content Types:**
- Single images
- Videos
- Carousel albums (multiple images/videos)

**Post Elements:**
- Image/video content
- Captions (with hashtags and mentions)
- Location tags
- User tags in media

### Rate Limits

**Status:** Inherits Facebook Graph API rate limits

**Important Considerations:**
- Business accounts have different limits than personal accounts
- Rate limits apply per user and per app
- Monitor API response headers for limit information

### Important Notes
- **Business/Creator Account Required:** Cannot post to personal Instagram accounts via API
- **Media Hosting:** Images must be hosted at publicly accessible URLs
- **Two-Step Process:** Container creation and publishing are separate API calls
- **No Official SDK:** Must use Facebook Graph API directly or via python-facebook
- **Alternative Libraries:** Community libraries exist but may violate Instagram ToS if using private API

---

## 4. Twitter API Client

### Package Information

- **Official Package:** `tweepy`
- **Installation:** `pip install tweepy`
- **Async Support:** `pip install tweepy[async]`
- **Latest Version:** v4.16.0 (released June 22, 2025)
- **Python Support:** Latest Python version and older versions not end of life
- **Repository:** https://github.com/tweepy/tweepy
- **Documentation:** https://docs.tweepy.org/

### Authentication Pattern

**OAuth 2.0 Bearer Token (App-Only):**

For Twitter API v1.1:
```python
import tweepy

auth = tweepy.OAuth2BearerHandler("Bearer Token here")
api = tweepy.API(auth)
```

Alternative using API key and secret:
```python
auth = tweepy.OAuth2AppHandler(
    "API / Consumer Key here",
    "API / Consumer Secret here"
)
api = tweepy.API(auth)
```

For Twitter API v2:
```python
import tweepy

client = tweepy.Client("Bearer Token here")
```

**OAuth 2.0 Authorization Code Flow with PKCE (User Context):**

Setup requirements:
1. Enable OAuth 2.0 in User authentication settings
2. Provide Callback/Redirect URI
3. Note Client ID (and Client Secret if confidential client)

```python
oauth2_user_handler = tweepy.OAuth2UserHandler(
    client_id="Client ID here",
    redirect_uri="Callback / Redirect URI / URL here",
    scope=["tweet.read", "tweet.write", "users.read"],
    client_secret="Client Secret here"  # Only for confidential clients
)

# Get authorization URL
print(oauth2_user_handler.get_authorization_url())

# After user authenticates, fetch token
access_token = oauth2_user_handler.fetch_token(
    "Authorization Response URL here"
)

# Use token with Client
client = tweepy.Client(access_token)
```

### Key Capabilities

**API Support:**
- Twitter API v1.1
- Twitter API v2 (recommended)
- Both synchronous and asynchronous clients

**Client Classes:**
- `Client` - Synchronous Twitter API v2 client
- `AsyncClient` - Asynchronous Twitter API v2 client
- `StreamingClient` - Real-time filtered stream
- `AsyncStreamingClient` - Async streaming

**Tweet Operations:**
- Create tweets
- Search tweets
- Manage timelines
- Likes, retweets, bookmarks
- Quote tweets
- Reply management

**Other Features:**
- User management (blocks, follows, mutes, lookup)
- Direct Messages lookup and management
- Lists management
- Spaces search and lookup
- Media upload
- Trends and geo information
- Compliance batch operations
- Pagination support

### Posting Tweets

**create_tweet() Method:**

```python
client = tweepy.Client(bearer_token="your_token")

response = client.create_tweet(
    text="Your tweet content here"
)
```

**Key Parameters:**
- `text` - Tweet content (required if media_ids not present)
- `media_ids` - List of Media IDs to attach
- `media_tagged_user_ids` - User IDs tagged in media
- `poll_options` & `poll_duration_minutes` - For creating polls
- `in_reply_to_tweet_id` - Reply to another tweet
- `quote_tweet_id` - Quote another tweet
- `reply_settings` - Control who can reply ("mentionedUsers", "following")
- `for_super_followers_only` - Restrict to Super Followers
- `place_id` - Geo location attachment
- `direct_message_deep_link` - Link to DM conversation
- `user_auth` - Whether to use OAuth 1.0a (default: True)

**Return Type:** `dict | requests.Response | Response`

**API Endpoint:** POST /2/tweets

### Character Limits

**Search Queries:**
- Standard Project (Basic): Up to 512 characters
- Academic Research Project: Up to 1,024 characters

**Tweet Length:**
- Standard tweets: 280 characters (enforced by Twitter, not SDK)
- Extended tweets available for certain account types

### Rate Limits

**Posting Tweets (POST /2/tweets):**

| Tier | Per User (15 min) | Per User (24 hr) | Per App (24 hr) |
|------|-------------------|------------------|-----------------|
| Pro  | 100 requests      | -                | 10,000 requests |
| Basic| -                 | 100 requests     | 1,667 requests  |
| Free | -                 | 17 requests      | 17 requests     |

**Recent Search (GET /2/tweets/search/recent):**

| Tier | Per User (15 min) | Per App (15 min) |
|------|-------------------|------------------|
| Pro  | 300 requests      | 450 requests     |
| Basic| 60 requests       | 60 requests      |
| Free | 1 request         | 1 request        |

**Rate Limit Tracking:**
- Response headers include:
  - `x-rate-limit-limit` - Total requests allowed
  - `x-rate-limit-remaining` - Requests remaining
  - `x-rate-limit-reset` - Time when limit resets
- When exceeded: HTTP 429 with error code 88

**Client Configuration:**
```python
client = tweepy.Client(
    bearer_token="your_token",
    wait_on_rate_limit=True  # Automatically wait when rate limit reached
)
```

### Best Practices

1. **Rate Limit Management:**
   - Cache responses when possible
   - Prioritize active users
   - Implement exponential backoff
   - Use `wait_on_rate_limit=True` for automatic handling

2. **Authentication:**
   - Use OAuth 2.0 Bearer Token for app-level operations
   - Use OAuth 1.0a User Context for per-user operations
   - Store tokens securely (environment variables, secure storage)

3. **Error Handling:**
   - Wrap API calls in try-except blocks
   - Handle HTTP 429 (rate limit exceeded)
   - Monitor response headers for rate limit status

4. **Async Support:**
   - Use `AsyncClient` for high-throughput applications
   - Better performance for concurrent operations

### Important Notes
- Twitter API v2 is recommended over v1.1
- Different access tiers (Free, Basic, Pro) have different rate limits
- Bearer tokens for app-level access, OAuth for user-level access
- Comprehensive documentation available at docs.tweepy.org
- Active maintenance and regular updates
- Supports both synchronous and asynchronous operations

---

## Summary and Recommendations

### Implementation Priority

1. **Twitter/X (Tweepy)** - READY TO IMPLEMENT
   - Well-documented, actively maintained
   - Clear rate limits and authentication patterns
   - Comprehensive SDK with async support
   - Straightforward posting API

2. **Xero** - READY TO IMPLEMENT (with caution)
   - Official SDK available
   - OAuth 2.0 well-documented
   - Rate limits need verification from official docs
   - Sample applications available for reference

3. **Facebook** - READY TO IMPLEMENT
   - Multiple SDK options available
   - python-facebook recommended for general use
   - facebook-python-business-sdk for advertising
   - Authentication well-documented

4. **Instagram** - REQUIRES ADDITIONAL RESEARCH
   - No official standalone SDK
   - Two-step posting process more complex
   - Requires Business/Creator account
   - Consider using python-facebook or direct API calls

### Security Considerations

**All SDKs:**
- Store credentials in environment variables
- Use OS-native secure storage for tokens
- Implement token refresh mechanisms
- Never commit credentials to version control
- Implement HITL approval for all posting operations

### Rate Limit Strategy

**Recommended Approach:**
1. Implement rate limit tracking in MCP servers
2. Cache API responses where appropriate
3. Use exponential backoff on rate limit errors
4. Monitor rate limit headers in responses
5. Implement queuing for high-volume operations

### Next Steps

1. **Verify Xero Rate Limits:** Contact Xero support or access developer portal
2. **Test Instagram Posting:** Prototype two-step container workflow
3. **Implement MCP Servers:** Create MCP servers for each SDK
4. **HITL Integration:** Ensure all posting operations require approval
5. **Dry-Run Mode:** Implement for all SDKs during development
6. **Audit Logging:** Log all API calls with parameters and results

---

## References

### Xero
- SDK Repository: https://github.com/XeroAPI/xero-python
- PyPI Package: https://pypi.org/project/xero-python/
- Sample Apps:
  - https://github.com/XeroAPI/xero-python-oauth2-starter
  - https://github.com/XeroAPI/xero-python-oauth2-app

### Facebook
- python-facebook: https://github.com/sns-sdks/python-facebook
- Business SDK: https://github.com/facebook/facebook-python-business-sdk
- Outdated SDK: https://github.com/mobolic/facebook-sdk (avoid)

### Instagram
- instagram_simple_post: https://github.com/remc0r/instagram_simple_post
- Use Facebook Graph API via python-facebook

### Twitter/X
- Tweepy Repository: https://github.com/tweepy/tweepy
- Documentation: https://docs.tweepy.org/
- PyPI Package: https://pypi.org/project/tweepy/
- Rate Limits: https://docs.x.com/x-api/fundamentals/rate-limits

---

**Report Generated:** 2026-01-19
**Research Conducted By:** Claude Code Agent
**Status:** Complete with noted limitations on Xero rate limits and Instagram implementation details
