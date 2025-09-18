FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    build-base \
    libffi-dev \
    openssl-dev

# Install uv
RUN pip install uv

# Copy pyproject.toml, pyproject.lock, and README.md first for better caching
COPY pyproject.toml pyproject.lock* README.md ./

# Install production dependencies only (no dev dependencies)
RUN uv pip install --system .

# Copy source code
COPY src/ ./src/
COPY server.py ./

# Copy CLI installation script
COPY scripts/install_cli.sh /tmp/install_cli.sh
RUN chmod +x /tmp/install_cli.sh

# Install CLI as root (before creating non-root user)
# This will download the correct architecture binary from GitHub releases
RUN /tmp/install_cli.sh

# Create a non-root user
RUN adduser -D -u 1000 cycloid

# Fix permissions for the cycloid user
RUN chown -R cycloid:cycloid /app && \
    chmod -R 755 /app

USER cycloid

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CY_CLI_PATH=/usr/local/bin/cy

# Run server directly with Python
CMD ["python3", "server.py"]
