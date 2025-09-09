# SolanaLM Dockerfile (Revised)

## Base Image
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

## Environment Variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON_VERSION=3.10
ENV SOLANA_VERSION=1.16.0

## Install System Dependencies
RUN apt-get update && apt-get install -y \
    python3.${PYTHON_VERSION} \
    python3-pip \
    curl \
    git \
    build-essential \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

## Install Rust (required for Anchor)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

## Install Solana CLI
RUN sh -c "$(curl -sSfL https://release.solana.com/v${SOLANA_VERSION}/install)"
ENV PATH="/root/.local/share/solana/install/active_release/bin:${PATH}"

## Install Node.js (required for Anchor)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

## Install Yarn (required for Anchor)
RUN npm install -g yarn

## Install Anchor
RUN cargo install --git https://github.com/coral-xyz/anchor avm --locked
RUN avm install latest
RUN avm use latest

## Set Working Directory
WORKDIR /app

## Copy Requirements
COPY requirements.txt .

## Install Python Dependencies
RUN pip3 install -r requirements.txt

## Copy Application Code
COPY . .

## Expose Ports
EXPOSE 8000  # Inference API
EXPOSE 8001  # Training Coordinator

## Default Command
CMD ["python3", "core/trainer/node.py"]