# syntax=docker/dockerfile:1

FROM python:3.10-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM python:3.10-slim

RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder --chown=appuser:appgroup /app /app

ENV PATH="/usr/local/bin:$PATH"
USER appuser

CMD ["python", "src/inference.py"]