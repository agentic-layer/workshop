
# Extras

## Flux - GitOps Delivery
Flux enables declarative, Git-based deployment of all platform components.

**Installation:**
```bash
flux bootstrap github \
  --token-auth \
  --owner=<your-github-username> \
  --repository=<your-repo-name> \
  --branch=main \
  --path=steps/06-extras/gitops \
  --personal
```

**What it does:**
- Continuously syncs Kubernetes manifests from your Git repository
- Ensures cluster state matches repository state
- Enables GitOps workflows for all subsequent installations

> [!TIP]
> Try to apply the Agents and ToolServer using gitops.

## Model Serving with Ollama

The Ollama models are deployed on the host vCluster. We sync the service
into the individual vClusters.

```bash
# start a local bash shell
kubectl run my-shell --rm -i --tty --image alpine -- /bin/sh
apk add curl
apk add bash

# call the chat API of Ollama or OpenAI
# curl http://ollama-model-llama31.default:11434/v1/chat/completions
curl http://ollama-model-llama31.default:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "messages": [
      {
        "role": "user",
        "content": "Say this is a test!"
      }
    ]
  }'
```