# yeswekanji-gcp: the Streamlit app for Cloud Run. Built by Cloud Build (tools/gcp/06-build.sh).
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv PYTHONUNBUFFERED=1
WORKDIR /app

# Dependencies first, in their own layer: rebuilt only when the lock changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-default-groups --no-install-project

COPY src/ ./src/

# Non-root user. Cloud Run sends traffic to $PORT (8080 by default).
RUN useradd --create-home app
USER app
ENV PORT=8080
CMD ["sh", "-c", "exec /app/.venv/bin/streamlit run src/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]
