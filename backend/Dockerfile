FROM python:3.11-slim

# Ensure CA certificates are available for SSL/TLS (e.g., Supabase Postgres)
# Also install OpenCV dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        libglib2.0-0 \
        libgtk-3-0 \
        libgl1 \
        libgstreamer1.0-0 \
        libgstreamer-plugins-base1.0-0 \
        libxrender1 \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Prefer IPv4 for network connections
RUN echo 'precedence ::ffff:0:0/96 100' >> /etc/gai.conf

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]