FROM python:3.11-slim

# Install required system packages (if any).  In a production build you
# may need to install compilers or OS libraries for specific ML
# frameworks.  We keep this minimal for portability.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
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

# Switch to non-root user
USER app

# Default command launches the bootstrap script via Uvicorn if no command provided
CMD ["python", "-m", "full_build.service.bootstrap"]