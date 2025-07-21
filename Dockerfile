# Use Python 3.11 slim as base (to match your requires-python)
FROM python:3.11-slim

# Set working directory
WORKDIR /app
# Set Python environment variables for better Docker performance
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# Install system dependencies for both PyQt5 and Playwright
RUN apt-get update && apt-get install -y \
    # PyQt5 dependencies
    qtbase5-dev \
    qtchooser \
    qt5-qmake \
    qtbase5-dev-tools \
    libqt5webkit5-dev \
    xvfb \
    # Playwright dependencies  
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    libappindicator3-1 \
    libu2f-udev \
    libwebkit2gtk-4.0-37 \
    libgtk-4-1 \
    libevent-2.1-7 \
    # Additional utilities
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration files first (for better caching)
COPY pyproject.toml .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

ENV PYTHONPATH=/app

# Set up FastAPI service
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
