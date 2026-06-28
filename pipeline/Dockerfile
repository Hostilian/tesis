# Use official Python slim image for a lightweight runtime
FROM python:3.12-slim

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for rasterio, geopandas, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    gdal-bin \
    proj-bin \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements list first to utilize Docker build layer caching
COPY requirements.txt .

# Install dependencies in the global container environment
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline source modules and orchestrator script
COPY src/ ./src/
COPY run_pipeline.py .

# Command to execute the pipeline by default
CMD ["python", "run_pipeline.py"]
