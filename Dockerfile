# syntax=docker/dockerfile:1

# =============================================================================
# Stage 1: Builder - Install dependencies and prepare environment
# =============================================================================
FROM python:3.10-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies for TensorFlow and OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY .python-version .

# Copy only the trained inference model (keep checkpoints out)
COPY models/sign_language_cnn.h5 ./models/sign_language_cnn.h5

# =============================================================================
# Stage 2: Production - Minimal runtime image
# =============================================================================
FROM python:3.10-slim-bookworm AS production

# Build arguments for metadata
ARG APP_VERSION=dev
ARG GIT_REVISION=unknown
ARG BUILD_DATE=unknown
ARG GITHUB_REPOSITORY=unknown

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
        && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appgroup && \
    useradd -r -u 1001 -g appgroup -s /bin/bash -d /home/appuser appuser

WORKDIR /home/appuser

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Copy application code
COPY --from=builder --chown=appuser:appgroup /app/src ./src
COPY --from=builder --chown=appuser:appgroup /app/.python-version .

# Copy trained model
COPY --from=builder --chown=appuser:appgroup /app/models/sign_language_cnn.h5 ./models/sign_language_cnn.h5

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TF_CPP_MIN_LOG_LEVEL=2

# OCI labels for container metadata
LABEL org.opencontainers.image.title="Sign to Speech" \
      org.opencontainers.image.description="Real-time sign language recognition using TensorFlow, OpenCV, and MediaPipe" \
      org.opencontainers.image.source="https://github.com/$GITHUB_REPOSITORY" \
      org.opencontainers.image.vendor="Sign to Speech Project" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="$APP_VERSION" \
      org.opencontainers.image.revision="$GIT_REVISION" \
      org.opencontainers.image.created="$BUILD_DATE"

# Switch to non-root user
USER appuser

# Expose ports (Jupyter notebook port if needed, inference port)
EXPOSE 8888 8000

# Health check (lightweight: verify model file is present)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.config import MODEL_PATH; import os; assert os.path.exists(MODEL_PATH)" || exit 1

# Default command - runs inference (webcam)
CMD ["python", "-m", "src.inference", "--model", "models/sign_language_cnn.h5", "--camera", "0"]
