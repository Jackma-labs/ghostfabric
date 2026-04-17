# DeepConf Expert Agent

DeepConf Expert Agent is a public reference implementation for building a codebase-specific expert on top of a base model such as `Qwen2.5-32B`.

It combines four ideas:

- `DeepConf-style decoding` to improve answer stability by sampling multiple reasoning paths and selecting higher-confidence results
- `RAG grounding` for internal code, docs, and operational notes
- `OpenAI-compatible tool-calling` for external agent shells
- `Constrained server-side agent execution` for safe file/code/config actions

This repository is meant to help teams build a practical domain expert, not a generic autonomous super-agent.

## Why DeepConf Helps

Base models often fail in two ways:

- they commit too early to a weak answer
- they answer with high confidence when evidence is incomplete

DeepConf improves this by generating multiple candidate traces, scoring them with token-level confidence, and selecting a stronger final answer instead of trusting a single pass.

In plain terms:

- a one-shot answer is one guess
- DeepConf is a small search procedure over multiple guesses
- confidence-aware selection makes it easier to keep the stronger trace and discard weaker drafts

This is useful for `Qwen2.5` because the model is often capable enough to produce a correct answer, but not always stable enough to choose that answer on the first try.

In practice this helps most on:

- code explanation
- technical Q&A
- multi-step reasoning
- cases where weak drafts should be filtered out

It does **not** magically solve missing evidence. That is where RAG and evaluation still matter.

## Why DeepConf Is Useful For Expert Mode

Expert mode usually fails for one of three reasons:

1. wrong retrieval
2. weak answer policy
3. overconfident final generation

DeepConf is most helpful on the third part. Once retrieval brings back relevant evidence, confidence-aware aggregation makes it easier to:

- prefer better grounded answers
- reduce noisy one-shot failures
- keep weak traces from dominating the final response

That is why this project treats expert mode as:

`retrieval quality + answer policy + confidence-aware decoding + strict evaluation`

DeepConf does not replace RAG. It helps most after retrieval has already surfaced relevant evidence.

The practical split is:

- `RAG` decides whether the model can see the right evidence
- `answer policy` decides whether weak evidence should trigger a conservative answer
- `DeepConf` improves the chance that the final answer is the stronger grounded one

## What Is Included

- `src/deepconf_proxy.py`
- `docs/architecture.md`
- `docs/safety.md`
- `SECURITY.md`
- `docs/expert-mode-training.md`
- `scripts/build_domain_assets.py`
- `scripts/expert_mode_pressure_test.py`
- `scripts/secret_scan.ps1`

## Deployment Modes

### 1. Reasoning proxy

Use `qwen2.5-32b-deepconf` style decoding to improve accuracy over a plain one-shot backend.

### 2. External agent provider

Use a tool-calling model endpoint that returns standard OpenAI `tool_calls` for clients such as WorkBuddy, Hermes, or OpenClaw.

### 3. Server-side expert agent

Use a constrained server-side tool runtime when you want the backend to perform safe reads, code search, and limited command execution.

## Safety Model

This repository intentionally does **not** expose unrestricted shell access.

The reference implementation uses:

- explicit allowed roots
- explicit allowed commands
- capped tool steps
- auditable write operations
- a recommendation for human approval on high-risk actions

Read `docs/safety.md` before using this in production.

The public proxy also includes:

- message sanitization for OpenAI-compatible inputs
- path allowlist validation
- command allowlist validation
- rejection of dangerous shell metacharacters in the reference command runner
- a pre-publish secret scan script

## Quick Start

1. Copy `examples/.env.example` to `.env`.
2. Replace placeholder values.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the proxy:

```bash
uvicorn src.deepconf_proxy:app --host 0.0.0.0 --port 7200
```

5. Check:

- `GET /health`
- `GET /v1/models`
- `POST /v1/chat/completions`

## Expert Training Workflow

The recommended workflow is:

1. Build a domain corpus.
2. Convert docs and troubleshooting notes into structured assets.
3. Build an evaluation set and an agent task set.
4. Improve retrieval before considering fine-tuning.
5. Add constrained tools only after scoring answer quality honestly.

The full method is documented in `docs/expert-mode-training.md`.

## Security Before Open Source

Do not publish:

- real API keys
- real IP addresses or SSH targets
- private corpus files
- internal usernames
- production config snapshots
- service logs with secrets or tokens

Use `scripts/secret_scan.ps1` as a last-pass guard, then still perform manual review.

## What This Repository Is Not

This is not:

- a claim that DeepConf alone makes any model an expert
- a fully autonomous production operator
- a replacement for retrieval quality, task design, and safety engineering

The intended open-source position is:

> A practical recipe for building a domain expert agent on top of Qwen2.5 with confidence-aware decoding, RAG grounding, and constrained execution.

## Pre-Publish Checklist

Before pushing:

1. Run `scripts/secret_scan.ps1`
2. Remove any real API keys, hosts, SSH material, usernames, or internal paths
3. Replace private corpora with redacted or synthetic examples
4. Review `.env.example` and docs for placeholders

## License

MIT
