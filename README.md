# RunPod Worker Image Background Removal

RunPod serverless worker untuk menghapus background gambar menggunakan rembg dengan GPU acceleration (CUDA 12.4).

## 📋 Fitur

- ✅ **Flexible Input Storage**: S3 atau RunPod Network Volume
- ✅ **Flexible Output Storage**: Cloudflare Images (CDN) atau Network Volume
- ✅ Background removal menggunakan berbagai model rembg (U2Net, BiRefNet, dll)
- ✅ Multi-format output: PNG (dengan transparansi), JPG, WebP dengan quality control
- ✅ Auto-delete input image setelah processing (opsional)
- ✅ Simpan metadata ke database PostgreSQL (opsional)
- ✅ Webhook callback async untuk notifikasi status (success/error)
- ✅ Model di-cache per session — tidak download ulang per request
- ✅ Model dibaca dari RunPod Network Volume via `U2NET_HOME`
- ✅ GPU acceleration via `rembg[gpu]` + CUDA 12.4 (CUDAExecutionProvider, no CPU fallback)

## 🖥️ System Requirements

### Hardware
- **GPU**: NVIDIA GPU dengan CUDA support
- **RAM**: Minimal 4GB
- **CPU**: Multi-core processor (4+ cores recommended)

### Software
- **Docker**: 20.10 atau lebih baru
- **Docker Compose**: 2.0 atau lebih baru
- **NVIDIA Container Toolkit**: Untuk GPU support di Docker

### Cloud (RunPod)
- **GPU Instance**: RTX 3080/3090, A4000, A5000, atau lebih tinggi
- **Disk Space**: Minimal 5GB
- **Network**: Akses ke S3 endpoint (input) dan Cloudflare API (output)

## 📦 Dependencies

### Python Packages
```
runpod              # RunPod serverless SDK
Pillow              # Image processing
rembg[gpu]          # Background removal (GPU-accelerated via onnxruntime-gpu)
boto3               # AWS S3 client
requests            # HTTP requests
sqlalchemy          # Database ORM
psycopg2-binary     # PostgreSQL driver
```

### Base Image
- `nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04`

### System Libraries
- libgl1 (OpenGL)
- libglib2.0-0 (GLib)

## 📁 Project Structure

```
runpod-worker-image-rembg/
├── main.py                  # RunPod handler & pipeline flow
├── remover.py               # rembg background removal logic
├── db/                      # Database module
│   ├── __init__.py          # Exports
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── service.py           # Database operations
│   └── migrations/          # SQL migrations
│       └── init.sql         # Initial schema
├── Dockerfile               # Container definition (CUDA 12.4)
├── docker-compose.yml       # Local development setup
├── requirements.txt         # Python dependencies
├── .env-example             # Environment template
├── .gitignore               # Git ignore rules
└── README.md                # Documentation
```

## 🔄 Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     RunPod Job Input                         │
│      { image, model, output_format, output_quality }         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   1. Validate Input                          │
│     Check image, model, output_format, output_quality        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         2. Load Image (S3 or Network Volume)                 │
│   • S3 mode: _download_image_from_s3()                       │
│   • Volume mode: _read_image_from_volume()                   │
│                 → PIL Image (RGB)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           3. Remove Background (GPU)                         │
│         ImageRemover.remove_background(image, model)         │
│                                                              │
│   • Session cached per model (no re-download per request)    │
│   • Reads model .onnx from U2NET_HOME (Network Volume)       │
│   • rembg.remove() → CUDAExecutionProvider (GPU only)        │
│   • Returns PIL Image (RGBA with transparency)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│       4. Save Result (Cloudflare or Network Volume)          │
│   • Cloudflare mode: _upload_to_cloudflare() → URL           │
│   • Volume mode: _save_image_to_volume() → Path              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│      5. Delete Input (Optional)                              │
│   if DELETE_INPUT_AFTER_UPSCALE: delete from S3/volume       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         6. Save to Database (Optional)                       │
│      if db_enabled: save_rembg_image(metadata)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         7. Send Webhook Callback (Async)                     │
│      POST to WEBHOOK_CALLBACK_URL with result                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Return Response                             │
│    { job_id, output_url, processing_time, ... }              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- NVIDIA Container Toolkit (untuk GPU support)
- Git

### 2. Clone & Setup

```bash
git clone <repository-url>
cd runpod-worker-image-rembg
cp .env-example .env
nano .env
```

### 3. Build Docker Image

```bash
docker compose build
```

### 4. Run Locally

Buat file `test_input.json` di root project:

```json
{
  "input": {
    "image": "folder/image.jpg",
    "model": "u2net",
    "output_format": "png"
  }
}
```

```bash
docker compose up
```

> **Note**: Lokal tanpa GPU akan error karena `CUDAExecutionProvider` tidak tersedia. Ini by design — worker hanya berjalan di GPU environment.

### 5. Deploy to RunPod

1. **Push image to Docker Hub**:
   ```bash
   docker build -t your-username/runpod-rembg:latest .
   docker push your-username/runpod-rembg:latest
   ```

2. **Create RunPod Serverless Template**:
   - Container Image: `your-username/runpod-rembg:latest`
   - Container Disk: 5GB minimum
   - Environment Variables: isi dari `.env`

3. **Deploy Endpoint**:
   - GPU Type: RTX 3080 atau lebih tinggi
   - Workers: sesuai kebutuhan
   - Attach Network Volume (untuk model rembg)

4. **Test via API**:
   ```bash
   curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "input": {
         "image": "folder/image.jpg",
         "model": "u2net",
         "output_format": "png"
       }
     }'
   ```

## 📦 Network Volume Setup — rembg Models

Model rembg **harus di-upload ke Network Volume** agar tidak di-download ulang setiap cold start. Worker membaca model dari `U2NET_HOME`.

### Download Model di Lokal

```bash
pip install rembg
python -c "from rembg import new_session; new_session('u2net')"
# Model tersimpan di ~/.u2net/u2net.onnx
```

Ulangi untuk model lain yang ingin digunakan (contoh: `birefnet-general`, `isnet-general-use`).

### Upload ke RunPod Network Volume

Upload file `.onnx` ke Network Volume melalui RunPod file manager atau SSH ke path:

```
/runpod-volume/u2net-models/
```

Struktur folder:
```
/runpod-volume/u2net-models/
├── u2net.onnx
├── u2netp.onnx
├── isnet-general-use.onnx
├── birefnet-general.onnx
└── ...
```

### Set Environment Variable

Set di RunPod Serverless Template:

```env
U2NET_HOME=/runpod-volume/u2net-models
```

Worker akan membaca model dari path ini. Jika file belum ada, rembg akan download otomatis ke path tersebut (hanya sekali).

### Upload Input Images (jika INPUT_STORAGE_MODE=volume)

```bash
mkdir -p /runpod-volume/inputs
scp -r /local/images/* user@pod:/runpod-volume/inputs/
```

## ⚙️ Configuration

### Environment Variables

#### Storage Configuration
```env
INPUT_STORAGE_MODE=s3                    # s3 or volume
INPUT_VOLUME_PATH=/runpod-volume/inputs/

OUTPUT_STORAGE_MODE=cloudflare           # cloudflare or volume
OUTPUT_VOLUME_PATH=/runpod-volume/outputs/

DELETE_INPUT_AFTER_UPSCALE=false
```

**Storage Modes**:

| Mode | Input | Output | Use Case |
|------|-------|--------|----------|
| **S3 + Cloudflare** | S3 bucket | Cloudflare Images CDN | External storage + CDN |
| **Volume + Volume** | Network Volume | Network Volume | All-in-one RunPod storage |
| **Volume + Cloudflare** | Network Volume | Cloudflare Images CDN | Bulk processing + CDN |
| **S3 + Volume** | S3 bucket | Network Volume | External input + local archive |

#### S3 Configuration (when INPUT_STORAGE_MODE=s3)
```env
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
S3_ENDPOINT_URL=https://your-s3-endpoint.com   # Optional, untuk non-AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

#### Cloudflare Images (when OUTPUT_STORAGE_MODE=cloudflare)
```env
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_API_TOKEN=your-api-token
```

**Output Paths**:
- **Cloudflare**: `upscale-results/YYYY/MM/DD/{uuid}.{ext}`
- **Volume**: `/runpod-volume/outputs/YYYY/MM/DD/{uuid}.{ext}`

#### rembg Model Location
```env
U2NET_HOME=/runpod-volume/u2net-models   # Path ke folder model .onnx di volume
```

#### Database (Optional)
```env
ENABLE_DATABASE=false
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

#### Webhook (Optional)
```env
WEBHOOK_CALLBACK_URL=https://your-api.com/webhook
WEBHOOK_TIMEOUT_SECONDS=10
WEBHOOK_AUTH_TOKEN=your-secret-token
```

#### Logging (Optional)
```env
LOG_LEVEL=INFO    # DEBUG, INFO, WARNING, ERROR
```

## 📡 API Reference

### Input Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `input.image` | string | Yes | - | Image path/key (S3 key or volume path) |
| `input.model` | string | No | `u2net` | Model rembg yang digunakan |
| `input.output_format` | string | No | `png` | Output format: `png`, `jpg`, `jpeg`, `webp` |
| `input.output_quality` | integer | No | 95 | Quality untuk lossy formats (1-100) |

**Notes**:
- S3 mode: `input.image` = S3 object key (`folder/image.jpg`)
- Volume mode: `input.image` = relative path dari `INPUT_VOLUME_PATH`
- PNG direkomendasikan — satu-satunya format yang mempertahankan transparansi

### Daftar Model

| Model | Keterangan |
|-------|-----------|
| `u2net` | General purpose (default) |
| `u2netp` | Lightweight version of u2net |
| `u2net_human_seg` | Optimized untuk segmentasi manusia |
| `u2net_cloth_seg` | Segmentasi pakaian |
| `silueta` | General purpose, alternatif u2net |
| `isnet-general-use` | IS-Net general purpose |
| `isnet-anime` | Optimized untuk gambar anime/ilustrasi |
| `birefnet-general` | BiRefNet general purpose (high quality) |
| `birefnet-general-lite` | BiRefNet lightweight |
| `birefnet-portrait` | Optimized untuk portrait/foto orang |
| `birefnet-dis` | Dichotomous image segmentation |
| `birefnet-hrsod` | High-resolution salient object detection |
| `birefnet-cod` | Camouflaged object detection |
| `birefnet-massive` | BiRefNet large model |
| `bria-rmbg` | BRIA background removal |

### Input Example

```json
{
  "input": {
    "image": "folder/photo.jpg",
    "model": "birefnet-portrait",
    "output_format": "png"
  }
}
```

### Success Response

```json
{
  "status": "success",
  "job_id": "job-12345",
  "processing_time": 1.2345,
  "input_storage_mode": "s3",
  "output_storage_mode": "cloudflare",
  "output_url": "https://imagedelivery.net/account-hash/image-id/public",
  "output_volume": null,
  "format": "png",
  "output_format": "png",
  "output_quality": null,
  "original_size": [1024, 768],
  "output_size": [1024, 768],
  "model": "birefnet-portrait",
  "webhook_triggered_at": "2026-05-03T10:30:45.123456+00:00",
  "error_message": null
}
```

### Error Response

```json
{
  "status": "error",
  "job_id": "job-12345",
  "error": "Unsupported model: invalid_model. Must be one of [...]",
  "error_message": "Unsupported model: invalid_model. Must be one of [...]",
  "webhook_triggered_at": "2026-05-03T10:30:45.123456+00:00"
}
```

### Webhook Callback

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <WEBHOOK_AUTH_TOKEN>
```

**Payload:** Same as response (success atau error)

## 🗄️ Database Schema

Table: `runpod_worker_rembg_images`

```sql
CREATE TABLE runpod_worker_rembg_images (
    id               SERIAL          PRIMARY KEY,
    job_id           TEXT,
    processing_time  DOUBLE PRECISION,
    original_url     TEXT            NOT NULL,
    output_url       TEXT            NOT NULL,
    model_name       TEXT            NOT NULL,
    original_width   INTEGER         NOT NULL,
    original_height  INTEGER         NOT NULL,
    output_width     INTEGER         NOT NULL,
    output_height    INTEGER         NOT NULL,
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
```

### Migration

```bash
psql $DATABASE_URL -f db/migrations/init.sql
```

## 🏗️ Code Architecture

### main.py
Orchestration & integration: S3, Cloudflare, webhook, database, error handling, response.

### remover.py
Background removal logic:
- `os.environ["U2NET_HOME"]` di-set **sebelum** `import rembg` — agar model dibaca dari volume, bukan di-download
- `_verify_gpu()` — startup check, **langsung error** jika GPU tidak tersedia (no silent CPU fallback)
- `_get_session(model)` — lazy load & cache session per model (tidak re-download per request)
- `new_session(model, providers=["CUDAExecutionProvider"])` — force GPU

## 🔧 Troubleshooting

### CUDAExecutionProvider not available

**Error**: `CUDAExecutionProvider not available. Available: ['CPUExecutionProvider']`

**Penjelasan**: Worker sengaja tidak fallback ke CPU. Error ini muncul jika run di lokal tanpa GPU.

**Solution**: Deploy ke RunPod GPU instance, atau jalankan Docker lokal dengan `--gpus all`.

### test_input.json not found

**Log**: `WARN | test_input.json not found, exiting.`

**Solution**: Buat file `test_input.json` di root project:
```json
{
  "input": {
    "image": "folder/image.jpg",
    "model": "u2net",
    "output_format": "png"
  }
}
```

### Model selalu download ulang

**Penjelasan**: `U2NET_HOME` tidak diset atau file `.onnx` belum ada di volume.

**Solution**:
1. Upload file `.onnx` ke `/runpod-volume/u2net-models/` di Network Volume
2. Set env var `U2NET_HOME=/runpod-volume/u2net-models` di RunPod Template

### S3 download failed

**Error**: `S3 download failed: NoSuchKey`

**Solution**: Verify `image` key, S3 credentials, `S3_BUCKET`, dan `S3_ENDPOINT_URL`.

### Cloudflare upload failed

**Error**: `403 Forbidden`

**Solution**: Verify `CLOUDFLARE_API_TOKEN` (permission: "Cloudflare Images: Edit") dan `CLOUDFLARE_ACCOUNT_ID`.

### Database connection failed

**Solution**: Check `DATABASE_URL` dan jalankan `db/migrations/init.sql`.

### Webhook timeout

**Solution**: Increase `WEBHOOK_TIMEOUT_SECONDS` dan verify `WEBHOOK_CALLBACK_URL`.

## 📊 Output Format

| Format | Transparansi | Keterangan |
|--------|--------------|-----------|
| PNG | ✅ Ya | **Direkomendasikan** — preserves transparency hasil background removal |
| WebP | ✅ Ya | Ukuran lebih kecil dari PNG |
| JPG | ❌ Tidak | Background area diganti warna putih otomatis |

## 📚 Resources

- [rembg GitHub](https://github.com/danielgatis/rembg)
- [BiRefNet GitHub](https://github.com/ZhengPeng7/BiRefNet)
- [RunPod Documentation](https://docs.runpod.io/)
- [Cloudflare Images Documentation](https://developers.cloudflare.com/images/)
- [NVIDIA CUDA Docker Images](https://hub.docker.com/r/nvidia/cuda)

## 📄 License

[Your License Here]

## 🤝 Contributing

Fork → feature branch → commit → Pull Request.

## 💬 Support

For issues or questions:
- Create GitHub issue
- Check existing documentation
- Review troubleshooting section
