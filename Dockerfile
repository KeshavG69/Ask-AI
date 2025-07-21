FROM python:3.13-slim

# Install minimal system dependencies and browser dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libnspr4 \
    libnss3 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libexpat1 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libcairo2 \
    libpango-1.0-0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip & install uv tool
RUN pip install --upgrade pip && pip install uv

# Install torch (CPU-only wheels)
RUN pip install torch==2.7.1 --extra-index-url https://download.pytorch.org/whl/cpu

# Install other Python dependencies
COPY pyproject.toml ./
RUN uv sync

RUN pip install playwright && playwright install chromium
# Set working directory & copy app code
WORKDIR /app
COPY . .

# Expose app on Render's dynamic port
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port $PORT"]
