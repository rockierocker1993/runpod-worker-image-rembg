FROM python:3.11-slim

WORKDIR /app

# System dependencies for Pillow / OpenCV used by rembg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

CMD ["python3", "-u", "main.py"]

