FROM python:3.12-slim

# Ensure CA certificates and minimal OpenCV dependencies for headless
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libglib2.0-0 \
        libgomp1 \
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