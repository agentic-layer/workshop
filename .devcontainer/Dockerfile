FROM debian:bookworm-slim

# Install basic tools
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    openssl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# Install flux CLI
RUN curl -s https://fluxcd.io/install.sh | bash

# Install k9s
RUN curl -sL https://github.com/derailed/k9s/releases/latest/download/k9s_Linux_amd64.tar.gz | tar xz -C /tmp \
    && mv /tmp/k9s /usr/local/bin/ \
    && chmod +x /usr/local/bin/k9s

# Verify installations
RUN kubectl version --client && \
    flux --version && \
    k9s version && \
    jq --version && \
    curl --version

# Set up non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && rm -rf /var/lib/apt/lists/*

USER $USERNAME

WORKDIR /workspace
