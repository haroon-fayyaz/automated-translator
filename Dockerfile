# syntax=docker/dockerfile:1

# ========= Base Image =========
FROM --platform=linux/amd64 python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/app/.local/bin:$PATH"

WORKDIR /app

# ========= Builder Stage =========
FROM base AS builder

# Install build deps for pip packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl wget gnupg2 unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome (amd64)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
    | gpg --dearmor -o /usr/share/keyrings/google-linux.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --upgrade pip \
    && pip install --user -r requirements.txt

# ========= Runtime Stage =========
FROM base AS runtime

# Install only Chrome runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgtk-3-0 \
    libnspr4 libnss3 libwayland-client0 libxcomposite1 libxdamage1 \
    libxfixes3 libxkbcommon0 libxrandr2 xdg-utils libu2f-udev \
    libvulkan1 xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy Chrome from builder
COPY --from=builder /usr/bin/google-chrome /usr/bin/google-chrome
COPY --from=builder /opt/google/chrome /opt/google/chrome

# Copy Python packages
COPY --from=builder /root/.local /home/app/.local

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app \
    && chown -R app:app /app \
    && mkdir -p /home/app/.cache/google-chrome \
    && mkdir -p /home/app/.config/google-chrome \
    && chown -R app:app /home/app

# ✅ Tell webdriver-manager to use home cache
ENV WDM_CACHE=/home/app/.cache/webdriver

# Create webdriver cache and fix permissions
RUN mkdir -p /app/webdriver_cache && chown -R app:app /app/webdriver_cache

USER app

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

