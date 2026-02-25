FROM python:3.11-slim

# System dependencies for Playwright + trafilatura
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only — ~130 MB)
# apt-get update is required here because the lists were cleaned in the previous layer
RUN apt-get update && playwright install chromium --with-deps && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8080

CMD ["uvicorn", "air_reader.main:app", "--host", "0.0.0.0", "--port", "8080"]
