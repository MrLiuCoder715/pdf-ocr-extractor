# ---- base: Python + uv + Tesseract (繁中 + 英文) ----
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS base
RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-chi-tra tesseract-ocr-eng \
 && rm -rf /var/lib/apt/lists/*
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./

# ---- test: dev deps + run the unit/functional suite (incl. real Tesseract tests) ----
FROM base AS test
RUN uv sync --frozen --no-install-project
COPY src ./src
COPY tests ./tests
RUN uv sync --frozen
CMD ["pytest", "-q", "-rs"]

# ---- runtime: production server ----
FROM base AS runtime
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev
RUN useradd --create-home appuser
USER appuser
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --timeout 300 'pdf_ocr_extractor.web:create_app()'"]
