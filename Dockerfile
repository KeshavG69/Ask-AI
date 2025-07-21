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
    # Missing libraries from error
    libgstreamer1.0-0 \
    libgtk-4-1 \
    libgraphene-1.0-0 \
    libatomic1 \
    libxslt1.1 \
    libvpx7 \
    libevent-2.1-7 \
    libopus0 \
    libavif15 \
    libenchant-2-2 \
    libsecret-1-0 \
    libmanette-0.2-0 \
    libgles2-mesa \
    # GStreamer plugins
    libgstreamer-plugins-base1.0-0 \
    libgstgl-1.0-0 \
    libgstcodecparsers-1.0-0 \
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

# Install only Chromium browser to keep image size smaller
RUN uv run playwright install chromium

# Copy application code
COPY . .

# Set display for headless browsers
ENV DISPLAY=:99

# Expose port for FastAPI
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uv", "run", "server.py"]
