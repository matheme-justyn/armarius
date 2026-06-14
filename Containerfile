# Containerfile for Armarius
# Multi-stage build using uv for fast dependency installation

FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install dependencies using uv
RUN uv pip install --system --no-cache -r pyproject.toml

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY armarius ./armarius
COPY i18n ./i18n
COPY pyproject.toml ./
COPY README.md ./

# Install armarius package
RUN pip install --no-deps -e .

# Create volume mount points
VOLUME ["/library", "/root/.armarius"]

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV ARMARIUS_LIBRARY_ROOT=/library
ENV ARMARIUS_WEB_PORT=8501
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health')" || exit 1

# Run Streamlit
CMD ["streamlit", "run", "armarius/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
