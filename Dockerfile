FROM python:3.13-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip & uv
RUN pip install --upgrade pip && pip install uv

# Install torch with CPU wheels only (saves GBs)
RUN pip install torch==2.7.1 --extra-index-url https://download.pytorch.org/whl/cpu

# Install other Python deps separately to leverage Docker caching
COPY pyproject.toml ./
RUN uv sync

# Install Playwright Chromium (this adds ~300MB)
RUN pip install playwright && playwright install chromium

# Create app directory & copy code
WORKDIR /app
COPY . .

# Expose dynamic port (Render/Heroku style)
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
