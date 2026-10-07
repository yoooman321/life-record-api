FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-install-project

COPY src/ /app/src/
COPY main.py README.md /app/
RUN uv sync --frozen
CMD ["sh", "-c", "exec uv run fastapi run main.py --host 0.0.0.0 --port $PORT"]