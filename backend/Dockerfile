# Dockerfile
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.cmd.main:app", "--host", "0.0.0.0", "--port", "8000"]