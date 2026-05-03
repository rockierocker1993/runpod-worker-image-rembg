-- DDL script for runpod-worker-image-rembg
-- PostgreSQL

CREATE TABLE IF NOT EXISTS runpod_worker_rembg_images (
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

CREATE INDEX IF NOT EXISTS idx_runpod_worker_rembg_images_created_at
    ON runpod_worker_rembg_images (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_runpod_worker_rembg_images_model_name
    ON runpod_worker_rembg_images (model_name);
