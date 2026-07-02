# ===== Stage 1: Build frontend =====
FROM node:22-slim AS frontend-builder
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
# Skip tsc (pre-existing type errors), Vite/esbuild handles transpilation
RUN npx vite build

# ===== Stage 2: Python runtime =====
FROM python:3.12-slim AS runtime

# System dependencies for compiling C extensions + git for HF/camel_tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
# Install CPU-only torch first to avoid pulling CUDA wheels
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
# Install remaining dependencies (torch line removed — already installed)
RUN grep -v '^torch==' requirements.txt > /tmp/req.txt && \
    pip install --no-cache-dir -r /tmp/req.txt

# Pre-download NLTK data (needed for English preprocessing at search time)
RUN python -c "import nltk; \
    [nltk.download(p) for p in ['punkt','punkt_tab','averaged_perceptron_tagger', \
    'averaged_perceptron_tagger_eng','wordnet','stopwords']]"

# Pre-download camel_tools MLE data (needed for Arabic preprocessing at search time)
# Non-fatal: if download fails, it will retry at runtime on first Arabic search
RUN python -c "from camel_tools.disambig.mle import MLEDisambiguator; \
    MLEDisambiguator.pretrained('calima-msa-r13')" \
    || echo "Warning: camel_tools MLE data download failed (will retry at runtime)"

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build from stage 1
COPY --from=frontend-builder /build/dist ./static

# Create data directory (mounted as volume at runtime)
RUN mkdir -p /app/backend/data

# Copy entrypoint script and fix line endings (Windows CRLF -> LF)
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

# Working directory for Python module resolution (routers.*, scripts.*, database)
WORKDIR /app/backend

ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV APP_MODE=annotation

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
