# Deploying AirReader on Railway

This guide walks you through deploying AirReader — a WhatsApp bot that reads and summarises web content — on [Railway](https://railway.app).

---

## Prerequisites

Before you start, make sure you have:

- A [Railway](https://railway.app) account
- A [Meta Developer](https://developers.facebook.com) account with a WhatsApp Cloud API app
- An [Anthropic](https://console.anthropic.com) API key
- (Optional) A [Google Custom Search](https://programmablesearchengine.google.com) API key and Search Engine ID, if you want Google search support

---

## Step 1 — Fork or push the repo to GitHub

Railway deploys directly from a GitHub repository.

1. Fork this repo to your GitHub account, **or** push it to a new private repo.
2. Make sure `railway.toml` is present at the root — it tells Railway to use the Dockerfile and sets the start command.

---

## Step 2 — Create a new Railway project

1. Go to [railway.app](https://railway.app) and click **New Project**.
2. Choose **Deploy from GitHub repo**.
3. Authorise Railway to access your GitHub account if prompted, then select the repo.
4. Railway will detect the `Dockerfile` automatically and begin the initial build.

> **Note:** The first build takes a few minutes because Playwright downloads a Chromium browser (~130 MB).

---

## Step 3 — Configure environment variables

In the Railway dashboard, open your service and go to **Variables**. Add each of the following:

### Required

| Variable | Description |
|---|---|
| `WHATSAPP_TOKEN` | Meta System User access token |
| `WHATSAPP_PHONE_NUMBER_ID` | Phone number ID from your WhatsApp app |
| `WHATSAPP_VERIFY_TOKEN` | A random secret string you choose — used to verify the webhook with Meta |
| `WHATSAPP_APP_SECRET` | App secret from your Meta app's **Settings → Basic** page |
| `ANTHROPIC_API_KEY` | Your Anthropic API key (`sk-ant-...`) |
| `ALLOWED_SENDER` | Your WhatsApp number in E.164 format **without** the leading `+`, e.g. `12125551234` |

### Search (choose one)

**Google Custom Search** (default):

| Variable | Description |
|---|---|
| `SEARCH_BACKEND` | Set to `google` |
| `GOOGLE_CSE_KEY` | Google API key |
| `GOOGLE_CSE_CX` | Custom Search Engine ID |

**Self-hosted SearXNG** (advanced — requires a separate SearXNG service):

| Variable | Description |
|---|---|
| `SEARCH_BACKEND` | Set to `searxng` |
| `SEARXNG_URL` | Internal URL of your SearXNG service, e.g. `http://searxng.railway.internal:8080` |

### Optional

| Variable | Default | Description |
|---|---|---|
| `CACHE_DB_PATH` | `air_reader_cache.db` | Path to the SQLite cache file. Set to `/data/air_reader_cache.db` if you add a persistent volume (recommended). |
| `CACHE_TTL_SECONDS` | `86400` | How long to cache fetched pages, in seconds (default 24 h). |

Railway automatically injects a `PORT` environment variable; the start command in `railway.toml` uses it, so you do not need to set `PORT` yourself.

---

## Step 4 — (Recommended) Add a persistent volume for the cache

Without a volume the SQLite cache is lost on every redeploy. To persist it:

1. In your service, go to **Settings → Volumes** and click **Add Volume**.
2. Set the mount path to `/data`.
3. Set `CACHE_DB_PATH` to `/data/air_reader_cache.db` in your Variables.

---

## Step 5 — Deploy and get your public URL

1. Trigger a deploy (Railway may have already started one after adding variables).
2. Once the deploy succeeds, go to **Settings → Networking** and click **Generate Domain** to get a public HTTPS URL, e.g.:
   ```
   https://air-reader-production.up.railway.app
   ```
3. Your webhook endpoint is:
   ```
   https://<your-railway-domain>/webhook
   ```

---

## Step 6 — Register the webhook with Meta

1. Open your app in the [Meta Developer Portal](https://developers.facebook.com/apps).
2. Go to **WhatsApp → Configuration**.
3. Under **Webhook**, click **Edit** and enter:
   - **Callback URL:** `https://<your-railway-domain>/webhook`
   - **Verify token:** the same value you set for `WHATSAPP_VERIFY_TOKEN`
4. Click **Verify and Save**. Meta will send a GET request to your webhook; Railway logs should show a `200 OK`.
5. Under **Webhook fields**, subscribe to **messages**.

---

## Step 7 — Send a test message

Send a WhatsApp message to your registered phone number. Try:

```
help
```

You should receive a reply listing the available commands. If you do not, check the Railway logs (**Deployments → View Logs**) for errors.

---

## Useful commands

```
url: https://example.com/article     # fetch and return full article text
sum: https://example.com/article     # fetch and summarise (medium length)
sum:short https://example.com/...    # short summary
sum:long https://example.com/...     # long summary
tl;dr: https://example.com/...       # alias for sum:short
search: your query                   # web search
help                                 # list all commands
```

---

## Troubleshooting

**Build fails with missing system dependencies**
Playwright's browser installation runs inside the Docker build. If it times out, trigger a fresh deploy — Railway will retry the build from cache.

**Webhook verification fails (Meta returns an error)**
- Double-check that `WHATSAPP_VERIFY_TOKEN` in Railway Variables exactly matches the value you entered in the Meta portal.
- Check Railway logs to confirm the app started successfully before attempting verification.

**Messages are received but no reply is sent**
- Ensure `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` are correct.
- Confirm `ALLOWED_SENDER` matches the number you are sending from (no `+`, just digits).
- Check Railway logs for Python tracebacks.

**Cache is not persisting between deploys**
Add a Railway volume mounted at `/data` and set `CACHE_DB_PATH=/data/air_reader_cache.db`.
