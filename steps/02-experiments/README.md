# Step 02: Evaluate Your Agent with an Experiment

You'll apply one or more **Experiment** CRs that run your agents against
a fixed dataset of inputs, score each response (deterministic string
checks + LLM-as-judge goal accuracy via RAGAS), and publish per-scenario
metrics to Mimir.

Prereq: [Step 01](../01-agentic-layer-runtime/) — the corresponding
agent(s) are running in your namespace:

- `cloudland-talks-experiment.yaml` needs the **cloudland-talks-agent**.
- `news-experiment.yaml` needs the **news-agent**.

Drop either resource from `kustomization.yaml` if you only deployed one
showcase in Step 01.

## Apply the Experiments

Open the YAML files in this folder and **manually replace every
`<your-namespace>` with your namespace** — same flow as Step 01. Skim
the scenarios in `spec.dataset.inline.scenarios` while you're there;
those are the test cases you're about to run.

```bash
kubectl apply -k steps/02-experiments
```

Behind the scenes the testbench-operator turns each `Experiment` CR
into a `TestWorkflow` in the `testkube` namespace:

```bash
kubectl get experiments -n $YOUR_NAMESPACE
testkube get testworkflow
```

Trigger an execution manually:

```bash
testkube run testworkflow cloudland-talks-experiment-$YOUR_NAMESPACE-workflow
```

> The `Experiment` CR also creates a `TestTrigger` on `spec.trigger.enabled`,
> but its label selector currently does not match the agent-runtime-operator's
> Deployment labels, so auto-trigger doesn't fire today. Use the CLI above.

List executions and tail the latest:

```bash
testkube get twe
```

A run with the default cloudland-talks-experiment scenarios completes in
about a minute — most of the wall time is LLM-as-judge calls.

## View results

Two surfaces:

**1. Mimir → Grafana.**

```bash
KUBECTL_PORT_FORWARD_WEBSOCKETS=true \
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
    - input: "What talks are on Wednesday?"
      reference:
        # StringPresence below checks this substring appears in the response.
        response: "2026-05-20"
      metrics:
        - metricName: StringPresence
          threshold: 1.0
        - metricName: AgentGoalAccuracyWithoutReference
```

Pair a deterministic substring anchor (`StringPresence`) with an
LLM-judged end-to-end check (`AgentGoalAccuracyWithoutReference`).
Re-apply the Experiment, then re-run `testkube run testworkflow ...`.

## Next

[Step 03 — PII Protection](../03-pii-protection/) — deploy your own
PII-guarded AI Gateway with Presidio, switch your agent over to it,
and watch the LLM responses change.
