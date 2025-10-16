FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory for the application
RUN mkdir -p /app/logs

# Copy and prepare the startup script
COPY start.sh .
RUN chmod +x start.sh

# Create non-root user and give ownership
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser $APP_HOME

USER appuser

# Expose the port (Railway uses the PORT env var)
EXPOSE 8000

# Set the startup command to our script
CMD ["/app/start.sh"]
