# Use Python 3.13 official image (Debian-based)
FROM python:3.13-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies for Playwright and missing libraries
RUN apt-get update && apt-get install -y \
    # Basic tools
    curl \
    git \
    wget \
    # Core browser dependencies
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    # Fonts
    fonts-liberation \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    # X11 and display
    xvfb \
    # Additional libraries that might be missing
    libglib2.0-0 \
    libdbus-1-3 \
    libxcb1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv - Fast Python package manager
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml ./
COPY uv.lock* ./
# Note: uv.lock might not exist yet, so we use uv.lock* to make it optional

# Install Python dependencies using uv
RUN uv sync

# Install Playwright browsers and system dependencies
RUN uv run playwright install

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set display for headless browsers
ENV DISPLAY=:99

# Expose port for FastAPI
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uv", "run", "server.py"]
