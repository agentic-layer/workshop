# Step 01: Deploy Your First AI Agents

Two self-contained showcases — pick whichever interests you, or do both:

- [`showcase-news/`](showcase-news/) — a **multi-agent** demo: news-agent
  delegates summarization to a sub-agent and calls an MCP news fetcher.
- [`showcase-cloudland-talks/`](showcase-cloudland-talks/) — a **single agent
  with multiple tools** demo: an agent that answers questions about the
  CloudLand 2026 conference programme. Ships with an `Experiment` you can
  exercise in [Step 04](../04-experiments/).

Everything else (operators, AI gateway, agent gateway, monitoring, LibreChat)
is already running cluster-wide — see [Step 00](../00-resource-and-platform-plane/).

## Apply

Skim the manifests in your chosen showcase folder, then replace the namespace
placeholder and apply. For the news showcase:

```bash
sed -i "s/<your-namespace>/$YOUR_NAMESPACE/g" steps/01-agentic-layer-runtime/showcase-news/*.yaml
kubectl apply -k steps/01-agentic-layer-runtime/showcase-news
```

For the CloudLand-talks showcase, swap `showcase-news` → `showcase-cloudland-talks`.

> macOS outside a Codespace: use `sed -i '' …` (BSD sed).

Verify:

```bash
kubectl get agents,toolservers,toolroutes,pods -n $YOUR_NAMESPACE
```

Three pods should reach `Running`. If one doesn't:

```bash
kubectl describe agent news-agent -n $YOUR_NAMESPACE
kubectl logs deployment/news-agent -n $YOUR_NAMESPACE
```

## Chat with your agent

```bash
kubectl port-forward -n librechat svc/librechat-librechat 3080:3080
```

Open <http://localhost:3080>, sign up with any email/password, pick the
**Agent Gateway** endpoint, and find your agent in the model list under
`$YOUR_NAMESPACE/...`. Try:

> What's the latest news in AI? Summarize the top article.   <!-- news-agent -->
> What AI talks are at CloudLand 2026?                        <!-- cloudland-talks-agent -->

## What's happening

```mermaid
graph LR
    User["👤 LibreChat"] -->|OpenAI API|Gateway["🚪 Agent Gateway"]
    Gateway -->|A2A|NewsAgent["📰 News Agent"]
    NewsAgent -->|tool|MCPServer["🔧 News Fetcher"]
    NewsAgent -->|A2A|Summarizer["📝 Summarizer"]
    Summarizer -->|tool|MCPServer
    NewsAgent -->|LLM|AI["🧠 AI Gateway"]
    Summarizer -->|LLM|AI
```

The operator turned your `Agent` / `ToolServer` YAML into Deployments + Services,
wired LLM calls to the shared AI Gateway (no API keys needed in your namespace),
registered the news-agent with the shared Agent Gateway (because `exposed: true`),
and auto-injected OTel so logs + traces show up in Grafana.

## Next

[Step 02 — Agent Gateway](../02-agent-gateway/): see how the gateway discovered
your agent. Or jump to [Step 04 — Experiments](../04-experiments/) to evaluate
the CloudLand-talks agent end-to-end.