"""
Docker configuration for FPTI application.
"""

# Dockerfile for backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY *.py ./

# Create data directory
RUN mkdir -p data

# Expose ports
EXPOSE 8000 8050

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV DATABASE_URL=sqlite:///./data/fpti.db

# Default command (can be overridden)
CMD ["python", "backend/main.py"]