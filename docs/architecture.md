# GhostFabric Architecture

## Overview

The GhostFabric system is split into four layers:

1. `Serving backend`
   Example: MindIE, vLLM, or another OpenAI-compatible inference backend hosting `Qwen2.5`.
2. `DeepConf proxy`
   Adds confidence-aware decoding, compatibility handling, and agent routing.
3. `RAG layer`
   Retrieves relevant code, docs, configs, logs, or operating notes.
4. `Agent client or server-side tools`
   Either the client executes tools, or the proxy executes a constrained built-in toolset.

## Why Confidence-Aware Decoding Improves Accuracy

One-shot decoding is fragile. A single poor reasoning path can dominate the final answer even when a better path exists.

DeepConf-style decoding improves this by:

- generating multiple candidate traces
- extracting token-level confidence from logprobs
- scoring each trace
- selecting a stronger answer based on confidence and agreement

This works especially well when:

- the task has a clearly better answer among multiple candidates
- weak reasoning traces should be filtered out
- the base model is capable but inconsistent

For `Qwen2.5`, this often matters more than adding a longer prompt. If the model already has the capability but occasionally locks onto a weak draft, confidence-aware selection can raise answer quality without changing the base weights.

## Expert Mode Stack

Expert mode should be treated as a stack, not a prompt:

1. `Question rewrite`
2. `Targeted retrieval`
3. `Grounded answer policy`
4. `Confidence-aware generation`
5. `Strict evaluation`

The key engineering point is that DeepConf mainly improves layer `4`. If layer `2` is weak, DeepConf will confidently choose among weak candidates. That is why retrieval and evaluation must be improved before claiming expert-level performance.

## Agent Modes

### External tool-calling mode

The proxy returns standard OpenAI `tool_calls`.

### Server-side built-in agent mode

The proxy executes a constrained internal toolset:

- `read_file`
- `write_file`
- `search_code`
- `run_command`

In a real deployment, each tool should be wrapped by:

- path validation
- argument schema validation
- audit logging
- timeout limits
- explicit risk tiers

## Recommended Production Boundaries

### Low risk

- code reading
- code search
- document retrieval
- log inspection
- status checks

### Medium risk

- repo-local file edits
- test execution
- non-destructive commands

### High risk

- `/etc` changes
- service restart
- network configuration
- system daemon changes
