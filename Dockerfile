# Dockerfile for resource_allocator (FastAPI)
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py ./
COPY resource_config.xml ./
COPY templates ./templates

# Expose the port FastAPI will run on
EXPOSE 8000

# Start the app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
