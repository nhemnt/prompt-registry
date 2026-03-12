FROM python:3.11-slim

WORKDIR /app

# Ensure we don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure python output is sent straight to terminal
ENV PYTHONUNBUFFERED=1
# Make the /app directory importable as a Python package root
ENV PYTHONPATH=/app

# Install required system dependencies if needed
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run migrations then start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
