FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (system deps already present in the base image)
RUN playwright install chromium

COPY . .

EXPOSE 8080

CMD ["uvicorn", "air_reader.main:app", "--host", "0.0.0.0", "--port", "8080"]
