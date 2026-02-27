# Deploying AirReader on Railway

This guide walks you through deploying AirReader — a WhatsApp bot that reads and summarises web content — on [Railway](https://railway.app).

---

## Prerequisites

Before you start, make sure you have:

- A [Railway](https://railway.app) account
- A [Meta Developer](https://developers.facebook.com) account with a WhatsApp Cloud API app
- An [Anthropic](https://console.anthropic.com) API key
- A search backend: either deploy SearXNG (included in this repo, recommended) or a [Google Custom Search](https://programmablesearchengine.google.com) API key and Search Engine ID (limited to specific sites on the free tier)

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

## Step 3 — Gather your credentials

Before entering anything in Railway, collect the values below. Each subsection explains exactly where to find them.

---

### 3a — WhatsApp Cloud API credentials

You need a Meta Developer account with a WhatsApp Cloud API app. If you have not set one up yet:

1. Go to [developers.facebook.com](https://developers.facebook.com) and log in.
2. Click **My Apps → Create App**.
3. Choose **Business** as the app type and follow the prompts.
4. Once the app is created, click **Add Product** and add **WhatsApp**.

**`WHATSAPP_PHONE_NUMBER_ID`**

1. In your app dashboard, go to **WhatsApp → API Setup**.
2. Under **Send and receive messages**, find the **Phone number ID** field (a long numeric string).
3. Copy that value.

**`WHATSAPP_TOKEN`**

This is a System User access token with `whatsapp_business_messaging` permission.

_Temporary token (fine for testing):_
1. On the same **WhatsApp → API Setup** page, under **Temporary access token**, click **Copy**. This token expires after 24 hours.

_Permanent token (recommended for production):_
1. Go to [business.facebook.com](https://business.facebook.com) → **Settings → Users → System Users**.
2. Create or select a System User, assign it the **Admin** role for your WhatsApp Business Account.
3. Click **Generate New Token**, select your app, and add the `whatsapp_business_messaging` permission.
4. Copy the generated token — it does not expire.

**`WHATSAPP_APP_SECRET`**

1. In your app dashboard, go to **Settings → Basic**.
2. Click **Show** next to **App Secret** and copy the value.

**`WHATSAPP_VERIFY_TOKEN`**

This is a value **you invent** — it is a shared secret between your app and Meta used only to confirm that webhook challenge requests come from Meta.

- Choose any random string, e.g. `my-secret-verify-token-123`.
- Save it somewhere; you will paste it into both Railway Variables and the Meta webhook configuration.

---

### 3b — Anthropic API key

**`ANTHROPIC_API_KEY`**

1. Go to [console.anthropic.com](https://console.anthropic.com) and sign in.
2. Navigate to **API Keys** in the left sidebar.
3. Click **Create Key**, give it a name, and copy the key (`sk-ant-...`).

> **Billing note:** You need to add a payment method under **Plans & Billing** before the key will work.

---

### 3c — Allowed sender

**`ALLOWED_SENDER`**

This is the phone number that is permitted to send commands to the bot. Only messages from this number will be processed.

- Use E.164 format **without** the leading `+`.
- Example: if your number is `+1 (212) 555-1234`, set the value to `12125551234`.

---

### 3d — Search credentials (choose one backend)

**Option A — Self-hosted SearXNG** (recommended)

The repo includes a ready-to-deploy SearXNG service in the `searxng/` directory. Deploy it as a second Railway service in the same project:

1. In your Railway project, click **+ New** → **GitHub Repo**.
2. Select the same repository.
3. Before deploying, click **Configure** → set **Root Directory** to `searxng`.
4. Give the service a name — use `searxng` (this becomes part of its internal URL).
5. Under the service **Variables**, add:
   - `SEARXNG_SECRET_KEY` — any random string, e.g. `openssl rand -hex 32`
6. Deploy the service. Railway will build the `searxng/Dockerfile` and start SearXNG.

Then in your **air-reader** service variables, set:
- `SEARCH_BACKEND=searxng`
- `SEARXNG_URL=http://searxng.railway.internal:8080`

Railway private networking lets the two services talk to each other without going through the public internet.

> **Note:** If you named the SearXNG service something other than `searxng`, replace `searxng` in the URL with that name, e.g. `http://my-searxng.railway.internal:8080`.

---

**Option B — Google Custom Search**

> **Warning:** Google Programmable Search Engine no longer offers a free "Search the entire web" option. You must manually list up to 50 domains to search, which limits the bot's usefulness. SearXNG (Option A) is strongly recommended instead.

If you still want to use Google:

`GOOGLE_CSE_KEY` — a Google Cloud API key:
1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create or select a project.
2. Navigate to **APIs & Services → Library** and enable **Custom Search API**.
3. Go to **APIs & Services → Credentials**, click **Create Credentials → API Key**, and copy the key.

`GOOGLE_CSE_CX` — a Custom Search Engine ID:
1. Go to [programmablesearchengine.google.com](https://programmablesearchengine.google.com).
2. Click **Add**, give the engine a name, and enter the specific sites you want to search.
3. Open the engine, go to **Overview**, and copy the **Search engine ID**.

Set `SEARCH_BACKEND=google`.

---

### 3e — Enter the variables in Railway

1. In your Railway project, click the service, then open the **Variables** tab.
2. Add each variable from the table below:

| Variable | Required | Value |
|---|---|---|
| `WHATSAPP_TOKEN` | Yes | System User access token |
| `WHATSAPP_PHONE_NUMBER_ID` | Yes | Numeric ID from WhatsApp API Setup |
| `WHATSAPP_VERIFY_TOKEN` | Yes | Random string you chose |
| `WHATSAPP_APP_SECRET` | Yes | From Meta app Settings → Basic |
| `ANTHROPIC_API_KEY` | Yes | `sk-ant-...` from Anthropic Console |
| `ALLOWED_SENDER` | Yes | Your number, digits only, no `+` |
| `SEARCH_BACKEND` | Yes | `searxng` (recommended) or `google` |
| `SEARXNG_URL` | If using SearXNG | `http://searxng.railway.internal:8080` |
| `GOOGLE_CSE_KEY` | If using Google | Google Cloud API key |
| `GOOGLE_CSE_CX` | If using Google | Custom Search Engine ID |
| `CACHE_DB_PATH` | No | `/data/air_reader_cache.db` (if using a volume) |
| `CACHE_TTL_SECONDS` | No | Seconds to cache pages, default `86400` (24 h) |

Railway automatically injects a `PORT` variable; the `railway.toml` start command uses it, so you do not need to set it yourself.

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
