# AirReader

A WhatsApp bot that fetches and summarizes web articles on demand. Send it a URL and get back the full article text, or ask for a summary at any length. Supports web search too.

**Commands:**
- `url: <link>` or bare URL — fetch full article
- `sum: <link>` — medium summary
- `sum:short: <link>` / `tl;dr: <link>` — 3–5 sentence summary
- `sum:long: <link>` — long summary (~half the article)
- `search: <query>` — web search, top 5 results
- `help` — show this list

---

## Deploy on Railway

### Prerequisites

- A [Railway](https://railway.app) account
- A [Meta developer account](https://developers.facebook.com) with a WhatsApp Cloud API app configured
- An [Anthropic API key](https://console.anthropic.com)
- (Optional) A Google Custom Search API key + engine ID, for the `search:` command

### 1. Create a new Railway project

1. Go to [railway.app](https://railway.app) and click **New Project**
2. Choose **Deploy from GitHub repo** and select this repository
3. Railway will detect the `Dockerfile` automatically — no extra build config needed

### 2. Add a persistent volume

SQLite needs durable storage so the cache survives redeploys.

1. In your Railway service, open the **Volumes** tab
2. Click **Add Volume**
3. Set the mount path to `/app/data`

### 3. Set environment variables

In the Railway service **Variables** tab, add:

| Variable | Required | Description |
|---|---|---|
| `WHATSAPP_TOKEN` | Yes | Meta system user access token |
| `WHATSAPP_PHONE_NUMBER_ID` | Yes | Phone number ID from Meta dashboard |
| `WHATSAPP_VERIFY_TOKEN` | Yes | Any random string — you'll use this when configuring the webhook |
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key (`sk-ant-...`) |
| `ALLOWED_SENDER` | Recommended | Your phone number in E.164 format (e.g. `12125551234`) — restricts the bot to only respond to you |
| `CACHE_DB_PATH` | Yes | Set to `/app/data/air_reader_cache.db` (matches the volume mount) |
| `SEARCH_BACKEND` | No | `google` (default) or `searxng` |
| `GOOGLE_CSE_KEY` | If using Google search | Google Custom Search API key |
| `GOOGLE_CSE_CX` | If using Google search | Google Custom Search engine ID |
| `SEARXNG_URL` | If using SearXNG | URL of your SearXNG instance |
| `CACHE_TTL_SECONDS` | No | Cache lifetime in seconds (default: `86400`) |

### 4. Deploy and get your public URL

Click **Deploy**. Once the build finishes, Railway assigns a public URL like:

```
https://your-app-name.up.railway.app
```

Your webhook endpoint is:

```
https://your-app-name.up.railway.app/webhook
```

### 5. Configure the Meta webhook

1. Open your app in the [Meta Developer Console](https://developers.facebook.com/apps)
2. Go to **WhatsApp → Configuration → Webhook**
3. Click **Edit** and fill in:
   - **Callback URL:** `https://your-app-name.up.railway.app/webhook`
   - **Verify token:** the value you set for `WHATSAPP_VERIFY_TOKEN`
4. Click **Verify and save**
5. Under **Webhook fields**, subscribe to **messages**

The bot is now live. Send a WhatsApp message to your test number to try it.

---

## Local development

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Run with Docker Compose (includes an optional SearXNG service):

```bash
docker-compose up
```

Or run directly (requires Python 3.11+ and Playwright Chromium installed):

```bash
pip install -r requirements.txt
playwright install chromium --with-deps
uvicorn air_reader.main:app --host 0.0.0.0 --port 8080 --reload
```

For local webhook testing, use a tunnel like [ngrok](https://ngrok.com):

```bash
ngrok http 8080
```

Then point the Meta webhook at the ngrok URL.
