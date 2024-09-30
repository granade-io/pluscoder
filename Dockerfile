# Build stage
FROM python:3.12-slim AS builder

# Install build essentials
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and wheels folder into the container
COPY requirements.txt .
COPY wheels /app/wheels

# Install the Python dependencies using local wheels and falling back to PyPI
RUN pip install --no-cache-dir --find-links=/app/wheels -r requirements.txt && \
    pip install --no-cache .

# Final stage
FROM python:3.12-slim

# Install git (required for the application)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy the application code
COPY . .

# Set the entrypoint to run pluscoder
ENTRYPOINT ["python", "-m", "pluscoder"]
