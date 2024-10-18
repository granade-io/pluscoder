# Build stage
FROM python:3.12-slim AS base

# Install build essentials
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
RUN mkdir /workspace
WORKDIR /workspace

# Copy the requirements file and wheels folder into the container
COPY requirements.txt .

# Install the Python dependencies using local wheels and falling back to PyPI
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS builder
# Install build dependencies
# TODO: Add build dependencies here
# COPY requirements-dev.txt .
# RUN pip install --no-cache-dir -r requirements-dev.txt
COPY pluscoder pluscoder
RUN pyinstaller --onefile --name pluscoder --add-data pluscoder/assets:assets pluscoder/__main__.py


# Final stage
FROM ubuntu:latest

# Application requirements
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy builded package from builder stage
COPY --from=builder /workspace/dist/pluscoder /bin/pluscoder

# Set the entrypoint to run pluscoder
ENTRYPOINT ["pluscoder"]
