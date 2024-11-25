# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install python venv
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy requirements file
COPY requirements.txt .

# Install dependencies in venv
RUN . /app/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Expose port
EXPOSE 8000

# Start the application using FastAPI
CMD ["/app/venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]