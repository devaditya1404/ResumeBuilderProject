# Multi-stage production Dockerfile for TalentVault AI FastAPI Backend
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (Poppler/PDF tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Expose port (Render/Railway default to PORT environment variable)
ENV PORT=8000
EXPOSE 8000

# Start production server with Uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
