# GhostFabric

<p align="center">
  <img src="assets/ghostfabric-wordmark.svg" alt="GhostFabric wordmark" width="860" />
</p>

<p align="center">
  <strong>Awaken dormant datacenter compute.</strong><br />
  Confidence-aware decoding, RAG grounding, and constrained agent execution for domain-specific expert systems.
</p>

<p align="center">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-111111.svg"></a>
  <a href="docs/safety.md"><img alt="Safety" src="https://img.shields.io/badge/safety-allowlist%20first-2f5d50.svg"></a>
  <a href="docs/expert-mode-training.md"><img alt="Training" src="https://img.shields.io/badge/expert%20mode-training%20guide-304b72.svg"></a>
  <a href="SECURITY.md"><img alt="Security" src="https://img.shields.io/badge/security-reviewed%20before%20publish-6b4f2a.svg"></a>
</p>

---

## Positioning

GhostFabric is a public reference implementation for teams who want to turn underused infrastructure into practical expert systems.

The target is not hobby hardware. The target is dormant datacenter compute: older accelerator fleets, legacy inference clusters, and environments where raw hardware still exists but software efficiency is lagging.

The technical core of GhostFabric is a `DeepConf Expert Agent` built around four layers:

- `confidence-aware decoding` to improve answer stability over one-shot generation
- `RAG grounding` for code, docs, configs, logs, and operational notes
- `OpenAI-compatible tool calling` for external agent clients
- `constrained server-side execution` for safe reads, search, edits, and bounded command execution

This repository is designed to help teams build a useful domain expert on top of models such as `Qwen2.5`, especially in environments where better inference orchestration can extract more value from existing compute.

---

## Why This Exists

Many organizations already have significant compute inventory, but a lot of it is underused because:

- model serving is unstable or poorly optimized
- retrieval is weak, so the model cannot behave like a real expert
- agent runtimes are unsafe or too brittle to trust
- legacy accelerator environments are treated as dead weight instead of optimization targets

GhostFabric takes the opposite view: older infrastructure can still be valuable if the serving path, retrieval stack, and execution policy are engineered carefully.

For legacy datacenter environments such as older `Ascend 910` deployments, the most practical wins often come from:

- better decoding policy
- better retrieval and evaluation
- better compatibility layers
- better operational guardrails

not just from buying new hardware.

---

## Why DeepConf Improves Qwen2.5

`Qwen2.5` is often strong enough to solve the task, but not always stable enough to choose the strongest answer on the first pass.

DeepConf helps by replacing one-shot trust with a lightweight search procedure:

1. generate multiple candidate traces
2. collect token-level confidence from logprobs
3. score candidate traces
4. stop early when one answer is clearly stronger
5. return the higher-confidence result

In practice, this improves:

- technical Q&A
- multi-step reasoning
- code explanation
- cases where one weak draft should not dominate the answer

It does **not** create missing evidence. If retrieval is weak, DeepConf will still be choosing among weak candidates. That is why this repository treats expert mode as a full stack problem:

`retrieval quality + answer policy + confidence-aware decoding + strict evaluation`

---

## Why DeepConf Is Useful For Expert Mode

Expert mode usually fails in one of three places:

1. the wrong evidence was retrieved
2. the answer policy was too loose
3. the final generation committed to a weak trace

DeepConf is most useful on the third part.

Once relevant evidence is present, confidence-aware aggregation makes it easier to:

- prefer better grounded answers
- filter weak one-shot drafts
- reduce noisy final outputs
- keep conservative behavior when evidence is thin

This makes it especially useful for codebase experts, operations assistants, and domain Q&A systems that need to be helpful without becoming reckless.

---

## System View

| Layer | Purpose | Example |
| --- | --- | --- |
| Serving backend | Host the base model | MindIE, vLLM, OpenAI-compatible backend |
| DeepConf proxy | Confidence-aware decoding and routing | `src/deepconf_proxy.py` |
| RAG layer | Surface relevant evidence | code, docs, configs, logs, runbooks |
| Agent runtime | Execute bounded actions | external `tool_calls` or constrained internal tools |

For a deeper view, read [docs/architecture.md](docs/architecture.md).
For a sharper project statement, read [Vision](docs/vision.md) and [Benchmark Framing](docs/benchmark.md).

---

## What You Get In This Repository

| File | Purpose |
| --- | --- |
| [src/deepconf_proxy.py](src/deepconf_proxy.py) | public DeepConf-style proxy reference |
| [docs/architecture.md](docs/architecture.md) | system design and production boundaries |
| [docs/safety.md](docs/safety.md) | safety rollout model and allowlist principles |
| [docs/expert-mode-training.md](docs/expert-mode-training.md) | how to build and evaluate expert mode |
| [docs/vision.md](docs/vision.md) | project thesis and positioning |
| [docs/benchmark.md](docs/benchmark.md) | what to measure and how to frame results |
| [SECURITY.md](SECURITY.md) | publishing and runtime security checklist |
| [scripts/build_domain_assets.py](scripts/build_domain_assets.py) | example asset builder for domain corpora |
| [scripts/expert_mode_pressure_test.py](scripts/expert_mode_pressure_test.py) | simple evaluation and latency harness |
| [scripts/secret_scan.ps1](scripts/secret_scan.ps1) | pre-publish secret scan |

---

## Deployment Modes

### 1. Reasoning Proxy

Use `qwen2.5-32b-deepconf` style decoding to improve answer quality over plain one-shot generation.

### 2. External Agent Provider

Expose standard OpenAI `tool_calls` to clients such as WorkBuddy, Hermes, or OpenClaw.

### 3. Server-Side Expert Agent

Execute bounded internal tools when you want the backend to perform safe reads, code search, limited edits, and allowlisted commands.

---

## Safety Model

This repository intentionally does **not** expose unrestricted shell access.

The public reference implementation uses:

- explicit allowed roots
- explicit allowed commands
- path validation
- rejection of shell chaining characters in the sample command runner
- capped execution patterns
- auditable write-oriented design
- a recommendation for human approval on high-risk actions

Read [docs/safety.md](docs/safety.md) and [SECURITY.md](SECURITY.md) before using this in production.

---

## Quick Start

1. Copy `examples/.env.example` to `.env`
2. Replace placeholders
3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Run the proxy

```bash
uvicorn src.deepconf_proxy:app --host 0.0.0.0 --port 7200
```

5. Verify the endpoints

- `GET /health`
- `GET /v1/models`
- `POST /v1/chat/completions`

---

## Expert Mode Training Workflow

The recommended order is:

1. build a domain corpus
2. convert docs and troubleshooting notes into structured assets
3. build a strict evaluation set and an agent task set
4. improve retrieval before fine-tuning
5. add constrained tools after honest scoring

The full method is in [docs/expert-mode-training.md](docs/expert-mode-training.md).

---

## Suitable Use Cases

- single-repository expert systems
- internal code and configuration assistants
- infrastructure troubleshooting copilots
- legacy accelerator deployment support
- datacenter inference efficiency projects

## Not The Goal

This repository is not:

- a claim that DeepConf alone makes any model an expert
- an unrestricted autonomous production operator
- a replacement for retrieval quality, evaluation, and safety engineering

---

## Brand Direction

`GhostFabric` reflects the actual operating thesis:

- dormant datacenter compute can be reactivated
- older accelerator fleets can still be useful
- serving, retrieval, and agent engineering can unlock production value without pretending old infrastructure is worthless

---

## Before You Publish A Fork

1. run `scripts/secret_scan.ps1`
2. remove real keys, hosts, usernames, and internal paths
3. remove private corpora and customer data
4. manually inspect the staged diff
5. review `.env.example`, screenshots, samples, and copied logs

---

## License

MIT
