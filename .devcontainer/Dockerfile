# syntax=docker/dockerfile:1.7
FROM debian:bookworm-slim

# Pinned tool versions. Bump together as a unit when refreshing the workshop.
# Helm and kubectl versions MUST include the leading "v".
ARG KUBECTL_VERSION=v1.36.1
ARG FLUX_VERSION=2.8.8
ARG K9S_VERSION=v0.50.18
ARG HELM_VERSION=v4.2.0
ARG TESTKUBE_VERSION=2.9.5

# Architecture is detected at build time via `dpkg --print-architecture`, which
# returns "amd64" or "arm64" — matching both kubectl's and k9s's URL conventions.
# We deliberately avoid `ARG TARGETARCH=<default>`: a default value silently
# overrides BuildKit's auto-populated TARGETARCH, baking amd64 into arm64 builds.

# Base packages. One apt block, --no-install-recommends, sudo merged in.
#   bash-completion — needed by the completion snippets at the end
#   procps          — provides `watch`, common during pod-status loops
#   less            — pager for kubectl logs and k9s
#   sudo            — vscode user needs passwordless sudo
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      jq \
      openssl \
      ca-certificates \
      git \
      bash-completion \
      procps \
      less \
      sudo \
    && rm -rf /var/lib/apt/lists/*

# kubectl — pinned, arch-aware (dpkg returns "amd64"/"arm64").
RUN ARCH="$(dpkg --print-architecture)" \
    && curl -fsSL -o /usr/local/bin/kubectl \
        "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${ARCH}/kubectl" \
    && chmod +x /usr/local/bin/kubectl

# flux CLI — install script auto-detects arch; FLUX_VERSION pins the release.
RUN curl -fsSL https://fluxcd.io/install.sh | FLUX_VERSION=${FLUX_VERSION} bash

# k9s — pinned, arch-aware (asset names use "amd64"/"arm64").
RUN ARCH="$(dpkg --print-architecture)" \
    && curl -fsSL "https://github.com/derailed/k9s/releases/download/${K9S_VERSION}/k9s_Linux_${ARCH}.tar.gz" \
      | tar -xz -C /tmp k9s \
    && mv /tmp/k9s /usr/local/bin/k9s \
    && chmod +x /usr/local/bin/k9s

# Helm v4 — install script auto-detects arch; --version pins the release.
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4 \
      | bash -s -- --version ${HELM_VERSION}

# testkube — install script auto-detects arch; ONLY the TESTKUBE_VERSION env var pins
# the release (positional args are ignored — script special-cases "beta" only).
RUN curl -fsSLf https://get.testkube.io | TESTKUBE_VERSION=${TESTKUBE_VERSION} bash

# Verify every installed tool actually runs in this image, offline (no kubeconfig).
# `testkube --help` is used in place of `testkube version` because the latter requires
# a server connection on 2.9.5 and may exit non-zero in the build sandbox.
RUN set -eux; \
    kubectl version --client; \
    flux version --client; \
    k9s version --short; \
    helm version --short; \
    testkube --help > /dev/null; \
    openssl version; \
    jq --version

# Non-root workshop user. apt and sudo install merged into the base block above.
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME \
    && echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Shell completions for the workshop user.
RUN set -eux; \
    mkdir -p /home/$USERNAME/.bash_completion.d; \
    kubectl completion bash    > /home/$USERNAME/.bash_completion.d/kubectl; \
    helm completion bash       > /home/$USERNAME/.bash_completion.d/helm; \
    flux completion bash       > /home/$USERNAME/.bash_completion.d/flux; \
    testkube completion bash   > /home/$USERNAME/.bash_completion.d/testkube; \
    { \
      echo ''; \
      echo '# Workshop tool completions'; \
      echo 'source /etc/bash_completion 2>/dev/null || true'; \
      echo 'for f in $HOME/.bash_completion.d/*; do [ -r "$f" ] && source "$f"; done'; \
      echo 'alias k=kubectl'; \
      echo 'complete -o default -F __start_kubectl k'; \
    } >> /home/$USERNAME/.bashrc; \
    echo '[ -f ~/.bashrc ] && . ~/.bashrc' > /home/$USERNAME/.bash_profile; \
    chown -R $USER_UID:$USER_GID \
        /home/$USERNAME/.bash_completion.d \
        /home/$USERNAME/.bashrc \
        /home/$USERNAME/.bash_profile

USER $USERNAME
WORKDIR /workspace
