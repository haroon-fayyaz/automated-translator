# syntax=docker/dockerfile:1

# ========= Base Image =========
FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/app/.local/bin:$PATH"

# ========= Builder Stage =========
FROM base AS builder

# Install build deps (only for compiling packages, won't stay in final image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --user --upgrade pip \
    && pip install --user -r requirements.txt

# ========= Runtime Stage =========
FROM base AS runtime

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app
USER app

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/app/.local

# Copy app source
COPY --chown=app:app . .

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
