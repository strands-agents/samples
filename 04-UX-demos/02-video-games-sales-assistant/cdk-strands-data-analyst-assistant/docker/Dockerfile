FROM public.ecr.aws/docker/library/python:3.13-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy entire project (respecting .dockerignore)
COPY . .

# Install dependencies

# Install from requirements file
RUN python -m pip install --no-cache-dir -r requirements.txt

# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

#RUN python -m pip install aws_opentelemetry_distro_genai_beta>=0.1.2

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

EXPOSE 8080

# Use the full module path from src directory
WORKDIR /app/src

#CMD ["opentelemetry-instrument", "python", "-m", "app"]
CMD ["python", "app.py"]
