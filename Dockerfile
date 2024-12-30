FROM python:3.12-slim

# Create non-root user
RUN useradd -m -s /bin/bash qubit

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set ownership to non-root user
RUN chown -R qubit:qubit /app

# Switch to non-root user
USER qubit

# Expose port
EXPOSE 8000 