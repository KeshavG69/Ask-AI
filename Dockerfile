FROM python:3.13-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip 

# Install Python dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Set working directory & copy app code
WORKDIR /app
COPY . .

# Expose app on Render's dynamic port
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port $PORT"]
