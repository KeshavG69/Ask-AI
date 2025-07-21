# Use Ubuntu 22.04 as base image for better library support
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies for Playwright and missing libraries
RUN apt-get update && apt-get install -y \
    # Python and basic tools
    python3.11 \
    python3.11-pip \
    python3.11-venv \
    python3.11-dev \
    curl \
    git \
    # Missing libraries for Playwright browsers
    libgtk-4-1 \
    libgraphene-1.0-0 \
    libgstgl-1.0-0 \
    libgstcodecparsers-1.0-0 \
    libavif15 \
    libenchant-2-2 \
    libsecret-1-0 \
    libmanette-0.2-0 \
    libgles2-mesa \
    # Additional browser dependencies
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
    fonts-noto \
    fonts-noto-color-emoji \
    # Additional multimedia libraries
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    # X11 and display
    xvfb \
    x11vnc \
    && rm -rf /var/lib/apt/lists/*

# Create Python 3.13 symlink (Ubuntu 22.04 has 3.11 by default)
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python

# Install uv - Fast Python package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml ./
COPY uv.lock* ./
# Note: uv.lock might not exist yet, so we use uv.lock* to make it optional

# Install Python dependencies using uv
RUN uv sync

# Install Playwright browsers and system dependencies
RUN uv run playwright install --with-deps

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
