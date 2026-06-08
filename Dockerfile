FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD [ "uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9092" ]