# Service Plane

## LibreChat

LibreChat is pre-deployed in the shared `librechat` namespace. Connect to it:

```bash
kubectl port-forward -n librechat svc/librechat-librechat 3080:3080
```

Open <http://localhost:3080>, sign up with any email/password, pick the
**Agent Gateway** endpoint, and find your agent — agents are prefixed with
their namespace (e.g. `ns-07/news-agent`).

If the port-forward drops, just re-run the command.

---

### Flowise 

Flowise is an "Open source agentic systems development platform"

```bash
kubectl apply -k steps/05-service-plane/flowise
```

Workshop Idea: Creating our own Flowise Node:
- Source Code: https://github.com/FlowiseAI/Flowise/tree/main/packages/components/nodes
- Tutorials: https://docs.flowiseai.com/getting-started#docker-image and https://docs.flowiseai.com/contributing/building-node


### Langflow

Langflow is a "Low-code AI builder for agentic and RAG applications"

```bash
kubectl apply -k steps/05-service-plane/langflow
```



