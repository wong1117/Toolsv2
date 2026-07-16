# Menggunakan image Python yang ringan
FROM python:3.11-slim

# Mencegah Python menulis file .pyc dan memastikan output log langsung tampil
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Mengatur direktori kerja di dalam container
WORKDIR /app

# Menginstal dependensi sistem operasi yang dibutuhkan (termasuk git untuk Orchestrator)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Menyalin file requirements terlebih dahulu untuk memanfaatkan Docker Cache
COPY requirements.txt .

# Menginstal pustaka Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh kode sumber platform ke dalam container
COPY ./platform ./platform

# Catatan: Kita tidak mendefinisikan CMD atau ENTRYPOINT di sini.
# Perintah eksekusi (uvicorn / python -m) akan diatur oleh docker-compose.yml
