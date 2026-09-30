FROM python:3.12-slim

WORKDIR /app

# Install review, testing, and HTTP service dependencies
RUN pip install --no-cache-dir ruff pytest fastapi uvicorn httpx

# Copy clean-room source, configuration, and tests
COPY . /app

# Expose port for HTTP service
EXPOSE 8000

# Health check to ensure service responds to HTTP requests
HEALTHCHECK --interval=5s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Serve the complete HTTP JSON API
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
