# Workshop: Architecting and Building a K8s-based AI Platform

This is the companion repository for a full-day workshop at the Continuous Lifecycle Conference in Mannheim on November 18, 2025.

## Abstract

Companies increasingly recognize the strategic importance of Artificial Intelligence, yet deploying AI solutions at scale presents significant challenges. This hands-on workshop provides a practical, step-by-step guide to designing and building a cloud-native AI platform.

You'll learn how to create a unified platform that simplifies the entire AI lifecycle using Kubernetes.

**What you'll build:**
- Agent runtime and orchestration layer
- API gateways for unified agent and model access
- Observability and monitoring stack

This repo guides you through the process of deploying agents onto a pre-provisioned AI platform.


## Overview

The cluster is shared across all participants. The platform (operators, gateways,
monitoring, LibreChat) is already deployed. You get **your own namespace**
(`ns-XX`) on the shared cluster to deploy your agents into.

- Step 0: Tour the pre-deployed platform
- Step 1: Deploy your first agents (and chat with them)
- Step 2: Evaluate your agent with an Experiment
- Step 3: Protect your prompts with a PII guardrail (Presidio)
- Step 4: (Bonus) GitOps + alternative UIs (Flowise, Langflow)

---

## Setup

1. **Fork** this repository.

2. **Create a GitHub Codespace** on your fork.

3. **Claim a namespace** by entering your name (or just an emoji) next to one of
   the `ns-XX` slots on this spreadsheet: https://ethercalc.net/mzku2p0zjwkk

4. **Decrypt the shared kubeconfig** (Kubernetes credentials file). The password
   will be announced during the workshop.

   ```bash
   ./decrypt-kubeconfig.sh kubeconfigs/workshop-kubeconfig.yaml.enc <password> kubeconfig.yaml
   ```

5. **Connect to the cluster**. Replace `ns-XX` with the namespace you claimed.

   ```bash
   export KUBECONFIG=kubeconfig.yaml
   export YOUR_NAMESPACE=ns-XX

   kubectl get pods -n $YOUR_NAMESPACE   # should be empty
   kubectl get namespace $YOUR_NAMESPACE  # confirms your namespace exists
   ```

6. **Start hacking!** Continue with [Step 0](steps/00-resource-and-platform-plane/).

---

## Port-forward tip

Every step that uses LibreChat or Grafana asks you to `kubectl port-forward`.
The connection dies on every server-sent-events close, so run it in a
retry loop (and force websockets, which are more tolerant of idle gaps):

```bash
while true; do
  KUBECTL_PORT_FORWARD_WEBSOCKETS=true \
    kubectl port-forward -n librechat svc/librechat-librechat 3080:3080
  sleep 1
done
```

Swap the namespace + service to forward Grafana (`monitoring`/`grafana 3000:80`)
or the observability dashboard (`observability-dashboard 8100:8000`).

---