FROM python:3.11-slim

# System dependencies for Playwright + trafilatura
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium and its runtime dependencies
# Use separate steps: install deps manually (Debian Trixie renamed some
# font packages that --with-deps expects), then install the browser.
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-unifont \
        fonts-liberation \
        fonts-noto-color-emoji \
        libnss3 libnspr4 libatk1.0-0t64 libatk-bridge2.0-0t64 \
        libcups2t64 libdrm2 libxkbcommon0 libxcomposite1 \
        libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
        libcairo2 libasound2t64 libatspi2.0-0t64 \
    && rm -rf /var/lib/apt/lists/*
RUN playwright install chromium

COPY . .

EXPOSE 8080

CMD ["uvicorn", "air_reader.main:app", "--host", "0.0.0.0", "--port", "8080"]
