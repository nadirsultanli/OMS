# Production Dockerfile with development dependencies
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy and install development dependencies (includes all needed packages)
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy app code
COPY . .

# Expose port
EXPOSE $PORT

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.cmd.main:app", "--host", "0.0.0.0", "--port", "$PORT"]