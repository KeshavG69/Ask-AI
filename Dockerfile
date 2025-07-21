# Use lightweight Python image
FROM python:3.13-slim

# Install only essential packages
RUN apt-get update && apt-get install -y \
    curl \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

WORKDIR /app

# Copy and install Python dependencies
COPY pyproject.toml ./
RUN uv sync

# Copy app code
COPY . .

# Configure Playwright to use system Chromium
ENV PLAYWRIGHT_BROWSERS_PATH=0
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

EXPOSE 8000
CMD ["uv", "run", "server.py"]
