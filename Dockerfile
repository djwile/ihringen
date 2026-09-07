FROM python:3.11-slim

# Create working directory inside the container
WORKDIR /app

# Install system packages your Python deps may need
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY app/ ./app
COPY wsgi.py .

# Expose the port Gunicorn will listen on
EXPOSE 8000

# Run Gunicorn
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8000"]