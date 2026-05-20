# Step 00: Tour the Pre-deployed Platform

The cluster is shared. The platform (operators, gateways, monitoring,
LibreChat) is already deployed via Flux. You only deploy your **own agents**
into your **own namespace**.

This step is a quick tour so you know what's available.

## Your namespace

```bash
# Set the Namespace in your Kubeconfig.
kubectl config set-context --current --namespace=$YOUR_NAMESPACE

kubectl get namespace $YOUR_NAMESPACE -o yaml
```

The `instrumentation.opentelemetry.io/inject-sdk` annotation means any pod
you create gets auto-instrumented — logs and traces flow into the shared
Grafana stack with no config.

## Operators (Custom Resource controllers)

```bash
kubectl get crd | grep agentic-layer.ai
```

Expected: `Agent`, `ToolServer`, `ToolRoute`, `AgenticWorkforce`,
`AgentGateway`, `AiGateway`.

- **Agent Runtime Operator** — reconciles `Agent` and `ToolServer` resources
  into Deployments + Services.
- **Agent Gateway KrakenD Operator** — reconciles `AgentGateway` resources
  (one cluster-wide gateway).
- **AI Gateway LiteLLM Operator** — reconciles `AiGateway` resources, routes
  LLM requests to providers.
- **Tool Gateway agentgateway Operator** — reconciles `ToolGateway` and
  `ToolRoute` resources.

## Shared platform services

```bash
kubectl get aigateway -n ai-gateway          # LLM proxy (LiteLLM)
kubectl get agentgateway -n agent-gateway    # OpenAI-compatible front door (KrakenD)
kubectl get toolgateway -n tool-gateway      # MCP tool aggregator
kubectl get pods -n monitoring               # Grafana, Loki, Tempo, Mimir, OTel collector
kubectl get pods -n librechat                # chat UI you'll use in Step 01
```

Your agents will use `model: gemini/gemini-2.5-flash` — that gets routed
through the AI Gateway, so **no API keys live in your namespace**.

## Troubleshooting

```bash
kubectl config current-context
kubectl cluster-info
```

## Next

[Step 01 — Deploy your agents](../01-agentic-layer-runtime/).