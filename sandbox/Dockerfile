FROM python:3.11-slim-bookworm

# Install system dependencies: curl, git
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Pre-install Python static analysis tools (for Phase 3)
RUN pip install --no-cache-dir \
    pylint \
    mypy

# Pre-install TypeScript / JavaScript tools (for Phase 3)
RUN npm install -g \
    typescript \
    eslint \
    @typescript-eslint/parser \
    @typescript-eslint/eslint-plugin

# Create workspace directory
WORKDIR /workspace

# Keep container running
CMD ["tail", "-f", "/dev/null"]
