# Expert Mode Training

## Core Idea

Do not start by fine-tuning the base model.

For a single repository or product domain, the most effective order is usually:

1. build the domain corpus
2. build retrieval assets
3. define answer policy
4. build a strict evaluation set
5. add constrained tools
6. consider fine-tuning only if needed

For many single-repository experts, `DeepConf + better retrieval + stricter evaluation` produces more practical gains than an early fine-tune.

## What To Collect

### Code

- source files
- config files
- launch scripts
- DAG definitions
- deployment scripts

### Documentation

- architecture docs
- module docs
- troubleshooting notes
- runbooks
- API docs

### High-value expert material

- engineer FAQ
- debugging notes
- correct operational steps
- known failure patterns
- boundary cases

## Convert Docs Into Three Asset Types

### 1. Retrieval corpus

- `title`
- `path`
- `source_url`
- `topic`
- `risk_level`
- `content`
- `commands`
- `paths`

### 2. Evaluation cases

- `question`
- `expectation`
- `keywords_hint`
- `source_path`
- `risk_level`

### 3. Agent tasks

- `title`
- `suggested_actions`
- `verification_targets`
- `risk_level`

## Why Retrieval Quality Matters More Than Prompt Size

Expert mode often fails because:

- the wrong document was retrieved
- the right document was retrieved too weakly
- the answer merged related but incorrect evidence

To improve retrieval:

- normalize aliases and synonyms
- boost exact title matches
- route by path scope
- rewrite user questions into domain language
- rank commands and config filenames more strongly

For troubleshooting corpora, it also helps to extract:

- common symptom phrases
- exact command snippets
- config file names
- service names
- expected outputs

## Answer Policy

### When evidence is strong

- answer directly
- include commands and paths when relevant
- state assumptions and constraints

### When evidence is weak

- say the evidence is insufficient
- explain the missing evidence
- suggest the next step

This is especially important for expert mode. A weak expert answer is often worse than a refusal because users may execute it on real systems.

## Strict Evaluation

Do not score an expert answer as correct just because:

- the HTTP request succeeded
- retrieval returned evidence

A stronger evaluation should require:

- response success
- no clearly conservative refusal language
- enough keyword hits
- ideally command/path coverage for operational questions

## When Fine-Tuning Is Worth It

Fine-tuning becomes worthwhile when:

- the domain has heavy jargon the base model repeatedly misunderstands
- the output format is stable and repetitive
- you already have high-quality Q&A pairs or agent traces

It is usually premature when:

- retrieval is still weak
- evaluation is still unstable
- the main failures are document selection failures

## What DeepConf Adds To Expert Mode

DeepConf is most helpful when:

- retrieval found multiple partially relevant chunks
- the base model can sometimes synthesize the right answer and sometimes miss it
- one-shot answers are noisy but not fundamentally impossible

DeepConf is less helpful when:

- no relevant evidence was retrieved
- the corpus is missing the answer entirely
- the task requires unsupported tools or permissions
