FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt
COPY agent.py .

EXPOSE 8080
CMD ["python", "agent.py"]
