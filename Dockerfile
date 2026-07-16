# Menggunakan image Python yang ringan
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# 1. Install dependencies sistem & Download Binary External Tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Semgrep & Checkov via Pip
RUN pip install --no-cache-dir semgrep checkov

# Download & Install Trivy
RUN wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor -o /usr/share/keyrings/trivy.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(. /etc/os-release && echo $VERSION_CODENAME) main" | tee /etc/apt/sources.list.d/trivy.list && \
    apt-get update && apt-get install -y trivy

# Download & Install Gitleaks
RUN wget -qO /usr/local/bin/gitleaks https://github.com/gitleaks/gitleaks/releases/download/v8.18.2/gitleaks_8.18.2_linux_x64.tar.gz && \
    tar -xzf /usr/local/bin/gitleaks -C /usr/local/bin gitleaks && \
    chmod +x /usr/local/bin/gitleaks && \
    rm /usr/local/bin/gitleaks

# Download & Install Dockle (Container Linter)
RUN wget -qO /usr/local/bin/dockle https://github.com/goodwithtech/dockle/releases/download/v0.4.14/dockle_0.4.14_Linux-64bit.tar.gz && \
    tar -xzf /usr/local/bin/dockle -C /usr/local/bin dockle && \
    chmod +x /usr/local/bin/dockle && \
    rm /usr/local/bin/dockle

# 2. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3. Copy source code
COPY ./platform ./platform
