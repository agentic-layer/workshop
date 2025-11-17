# Service Plane

Let's install a "Service Plane" for users!


## LibreChat!

First, let's deploy LibreChat as a way to talk to our agents.

Steps:
1. Follow the instructions at https://www.librechat.ai/docs/local/helm_chart#configuration to generate credentials for a fresh Helm Chart-based installation of Librechat
2. Create a new `Secret` file with the given credentials and apply it to your cluster. Use `librechat-credentials-env` as the name and `librechat` as the namespace.
3. Apply the prepared ConfigMap to let LibreChat know how to find our agents. Note you might need to change the name of the ConfigMap if the pod ends up not starting:

```bash
kubectl apply -k steps/05-user-serving-plane/librechat/
```

4. Install the LibreChat helm chart with the included `values.yaml` file

```bash
helm install librechat oci://ghcr.io/danny-avila/librechat-chart/librechat --values steps/05-user-serving-plane/librechat/values.yaml --namespace librechat
```

5. Open a port-forward and talk to the models!


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



