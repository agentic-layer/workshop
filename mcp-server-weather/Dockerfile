FROM python:3.14-slim-trixie

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --link-mode=copy

COPY server.py ./

EXPOSE 8000

ENTRYPOINT ["uv", "run", "--no-sync", "fastmcp", "run", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000", "server.py"]
CMD []
