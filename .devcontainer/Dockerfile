FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

USER vscode
WORKDIR /home/vscode

RUN sudo apt-get update \
    && sudo apt-get install -y --no-install-recommends \
        awscli \
    && sudo apt-get clean \
    && sudo rm -rf /var/lib/apt/lists/*

# Install SAM CLI
ADD --chown=vscode:vscode primary-public-key.txt signer-public-key.txt install-sam.sh ./

RUN chmod +x ./install-sam.sh \
    && ./install-sam.sh \
    && rm -f ./primary-public-key.txt ./signer-public-key.txt ./install-sam.sh

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
