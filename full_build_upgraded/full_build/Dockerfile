FROM python:3.13-slim

# Install required system packages including wget for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        wget \
        && rm -rf /var/lib/apt/lists/*

# Create unprivileged user
RUN adduser --disabled-password --gecos "" app

WORKDIR /app

# Copy source code and configuration
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose the default API port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8000/health || exit 1

# Switch to non-root user
USER app

# Default command launches the API via Uvicorn
CMD ["uvicorn", "full_build.service.api:app", "--host", "0.0.0.0", "--port", "8000"]