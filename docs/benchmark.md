# Benchmark Framing

## Why Benchmark This Project

GhostFabric is not trying to win a benchmark that ignores deployment reality. The point is to make older datacenter inference infrastructure more useful.

That means evaluation should measure:

- answer quality under real retrieval
- latency under realistic sampling policies
- agent task completion under constrained execution
- operational value on legacy accelerator environments

## Recommended Benchmark Axes

### 1. Expert answer quality

Measure:

- strict pass rate on a fixed expert evaluation set
- refusal accuracy on boundary questions
- command and path coverage for operational questions

### 2. DeepConf uplift

Compare:

- one-shot backend
- DeepConf with low sample count
- DeepConf with moderate sample count

Track:

- pass rate delta
- conservative failure delta
- latency cost

### 3. Retrieval quality

Measure:

- title hit rate
- command hit rate
- path hit rate
- evidence sufficiency rate

### 4. Agent reliability

Measure:

- tool-call success rate
- verification success rate
- rollback requirement rate
- blocked unsafe action rate

## Legacy Accelerator Narrative

For older clusters such as legacy `Ascend 910` deployments, GhostFabric should be evaluated as an efficiency layer:

- can existing hardware serve useful workloads again
- can weaker environments still produce acceptable expert behavior
- can engineering quality compensate for unstable one-shot generation

This is the benchmark story worth publishing.
