
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder /app/.venv ./.venv
COPY app ./app
COPY static ./static
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
