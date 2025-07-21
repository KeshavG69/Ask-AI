# Use official Playwright image which has all browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

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
