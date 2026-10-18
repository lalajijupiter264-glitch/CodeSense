FROM python:3.12-slim-bookworm

# Install OpenJDK 17 and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Verify OpenJDK javac installation
RUN javac -version

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
