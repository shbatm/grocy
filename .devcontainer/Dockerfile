ARG VARIANT="debian"
FROM mcr.microsoft.com/vscode/devcontainers/base:${VARIANT}

# Install system packages needed for building Python packages and Home Assistant tests
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      python3-dev \
      python3-venv \
      python3-pip \
      python3-distutils \
      python3-full \
      git \
      curl \
      jq \
      ca-certificates \
      libssl-dev \
      libffi-dev \
      libjpeg-dev \
      zlib1g-dev \
      pkg-config \
      cargo \
    && rm -rf /var/lib/apt/lists/*
