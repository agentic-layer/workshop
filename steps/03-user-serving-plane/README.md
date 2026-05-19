# Service Plane

Alternative agentic-system UIs you can try on top of your deployed agents.
LibreChat is already covered in step 01 — these are bonus exploration options.

### Flowise

Flowise is an "Open source agentic systems development platform"

```bash
kubectl apply -k steps/03-user-serving-plane/flowise
```

Workshop Idea: Creating our own Flowise Node:
- Source Code: https://github.com/FlowiseAI/Flowise/tree/main/packages/components/nodes
- Tutorials: https://docs.flowiseai.com/getting-started#docker-image and https://docs.flowiseai.com/contributing/building-node

### Langflow

Langflow is a "Low-code AI builder for agentic and RAG applications"

```bash
kubectl apply -k steps/03-user-serving-plane/langflow
```