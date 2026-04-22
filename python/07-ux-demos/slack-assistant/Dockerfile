FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 3000

CMD ["gunicorn", "app:api_with_health", "-b", "0.0.0.0:3000"]
