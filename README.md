# Multi-Agent AppSec Automation Platform

Platform otomasi keamanan aplikasi terpusat yang memanfaatkan arsitektur *microservices*, *Retrieval-Augmented Generation* (RAG), dan agen AI lokal (Ornith & Qwythos) untuk melakukan triase, verifikasi, dan remediasi temuan pemindai keamanan secara asinkron.

## Arsitektur Inti
- **API & Gateway:** FastAPI (Python)
- **Database Relasional:** PostgreSQL 15
- **Message Broker:** Redis 7
- **Object Storage:** MinIO (S3 Compatible)
- **Vector Database:** Qdrant
- **AI Engine:** Ollama (Llama 3)
- **Workers:** Python Asyncio & Redis Queue

---

## 📋 Prasyarat Sistem

Sebelum memulai, pastikan sistem Anda telah memiliki:
1. **Docker & Docker Compose** versi terbaru.
2. **NVIDIA Container Toolkit** terinstal dan terkonfigurasi (Wajib untuk mengaktifkan akselerasi perangkat keras pada RTX 4090 agar inferensi agen AI berjalan optimal dan memanfaatkan 24GB VRAM).
3. **Git** (untuk *Orchestrator Worker* mengunduh repositori target).

---

## ⚙️ Langkah Instalasi & Konfigurasi

### 1. Kloning Repositori & Persiapan Direktori
Pastikan struktur folder sudah sesuai dengan desain platform:
```bash
git clone <url-repositori-anda> appsec-platform
cd appsec-platform
