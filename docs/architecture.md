# Architecture

## Goal

`vex` should unify the Python AI app workflow without inventing a parallel packaging ecosystem.

It should explicitly build on top of `uv`, not compete with `uv`.

## MVP Principles

1. Use `pyproject.toml` as the source of truth.
2. Default to a local `.venv` per project.
3. Prefer delegation to mature tools over reimplementation.
4. Keep the command surface small.
5. Optimize for AI app developers first.
6. Treat runtime choice, policy, and model packaging as first-class workflow concerns.

## Recommended Integration Stack

### Core Substrate

- `uv`
  - Python installation and pinning
  - virtual environment creation
  - dependency add/remove/lock/sync
  - command execution
  - build and publish delegation
  - isolated tool execution
### AI Workflow Layer

- `vex-ai-runtime`
  - secure packaged model artifacts
  - native inference execution
  - runtime policy enforcement
- local model runtimes like `ollama`
  - local development and fallback execution paths
- eval and benchmark adapters
  - local-first quality and performance loops
- `watchfiles`
  - generic dev reload support for AI apps

### Later Phase

- deployment adapters for Modal, BentoML, Baseten, or OCI-first workflows
- policy-aware packaging for agent and model artifacts
- richer local benchmark and eval integrations

## Non-Goals

- custom dependency resolver
- custom lockfile format in v0
- custom build backend
- a generic replacement for `uv`
- a new general-purpose Python runtime in the initial `vex` product

## Why AI Workflow Is The Better Wedge

`uv` already solved a large part of generic Python workflow. The remaining open space is higher-level and AI-specific:

- local-first AI app workflow is still fragmented
- model packaging and execution policy are not first-class in generic Python tools
- deployment and runtime choices are still split across many products
- AI app packaging is not the same thing as Python dependency management

The better wedge for `vex` is an AI-native workflow layer that can later orchestrate `vex-ai-runtime` and other execution backends.
