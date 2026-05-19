# Step 02: Evaluate Your Agent with an Experiment

You'll define an **Experiment** that runs your agent against a fixed
dataset of inputs, scores each response (tool-call accuracy, topic
adherence, goal accuracy via LLM-as-judge), and publishes per-scenario
metrics to Mimir.

Prereq: [Step 01](../01-agentic-layer-runtime/) — at least one agent is
running in `$YOUR_NAMESPACE`.

## Apply the Experiment

The cloudland-talks showcase ships with one:
[`cloudland-talks-experiment.yaml`](../01-agentic-layer-runtime/showcase-cloudland-talks/cloudland-talks-experiment.yaml).
It evaluates the `cloudland-talks-agent` against three scenarios — a
specific-talk lookup, a category filter, and an off-topic refusal test.

If you applied the whole `showcase-cloudland-talks/` kustomization in
step 01, the Experiment is already created — skip to **Trigger** below.
Otherwise:

```bash
kubectl apply -f steps/01-agentic-layer-runtime/showcase-cloudland-talks/cloudland-talks-experiment.yaml
```

The testbench-operator turns the `Experiment` CR into a `TestWorkflow`
in the `testkube` namespace:

```bash
kubectl get testworkflow -n testkube
```

## Trigger an execution

```bash
testkube run testworkflow cloudland-talks-experiment-$YOUR_NAMESPACE-workflow
```

The CLI prints an execution ID. Watch progress with:

```bash
testkube get twe <execution-id>
```

A run takes 5–10 min depending on how many LLM-as-judge calls fire.

## View results

Two surfaces:

**1. Mimir → Grafana.** Open Grafana:

```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
```

→ <http://localhost:3000> → **Explore** → pick the Mimir datasource → try:

```promql
testbench_evaluation_metric{experiment_name="cloudland-talks-experiment"}
```

Each series is one (scenario, metric) combination. `result="pass"` /
`result="fail"` is a label; the value (0 or 1) is the score.

For pass-rate trends and per-execution breakdowns, open the
**Testkube** dashboard from the Grafana sidebar.

**2. HTML report.** Each execution writes an evaluation report:

```bash
testkube get twe <execution-id> --download-artifacts
open artifacts/data/results/evaluation_report.html
```

## Author your own scenarios

The Experiment CRD's `spec.dataset.inline.scenarios` is a list of
input/reference pairs. The simplest scenario:

```yaml
- name: "My first scenario"
  steps:
    - input: "What's on Wednesday?"
      reference:
        topics: [cloudland-talk]
      metrics:
        - metricName: AgentGoalAccuracyWithoutReference
        - metricName: TopicAdherence
          parameters: { mode: precision }
```

Re-apply the Experiment, then re-run `testkube run testworkflow ...`.

## Next

[Step 03 — User-Serving Plane](../03-user-serving-plane/) — alternative
UIs (Flowise, Langflow) for your agents.
