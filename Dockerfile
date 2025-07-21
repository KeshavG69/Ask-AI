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

# Install Playwright Chromium
RUN uv run playwright install chromium

# Copy app code
COPY . .

EXPOSE 8000
CMD ["uv", "run", "server.py"]
