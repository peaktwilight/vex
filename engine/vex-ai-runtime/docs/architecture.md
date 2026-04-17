# Architecture

## Product Goal

Build a secure, fast Python inference runtime that narrows scope aggressively:

- ONNX-first
- CPU-first for MVP
- Python API on top of a native Rust core
- strong packaging and sandbox defaults

The first product is not a general Python replacement. It is a better execution and packaging path for inference-heavy Python applications.

## Why ONNX Runtime First

The best MVP choice is ONNX Runtime under a Rust wrapper because it optimizes for the hardest early constraint: compatibility.

Why this wins for MVP:

- broad ONNX compatibility
- proven native engine
- stable C API for Rust wrapping
- supports minimal and reduced-op builds
- lets us focus on packaging, cold start, and security instead of model compatibility firefighting

Deferred alternatives:

- `tract`: attractive Rust-native future path, but narrower ONNX coverage
- `candle`: attractive for model-family-specific runtimes later
- `llama.cpp`: useful for GGUF-specific products, not the general ONNX wedge

## Core Layers

### 1. Python API Layer

Responsibilities:

- ergonomic model/session interface
- input/output validation at the Python boundary
- artifact loading and configuration
- developer-friendly errors

This layer should remain thin.

### 2. Rust Runtime Core

Responsibilities:

- load packaged model artifacts
- configure ONNX Runtime sessions
- manage memory-sensitive runtime settings
- expose safe, typed operations to Python
- enforce security defaults before model execution

The Rust layer is where the trusted runtime policy should live.

### 3. Model Packaging Pipeline

Responsibilities:

- validate incoming ONNX models offline
- convert eligible models to optimized artifacts later
- record metadata, hashes, and allowed runtime settings
- produce reproducible runtime bundles

This should be an explicit build step, not an implicit runtime side effect.

## Security Defaults

MVP security posture:

- packaged model artifacts are trusted inputs; arbitrary runtime model loading is deferred
- no automatic network access for model fetches in the runtime core
- explicit filesystem paths only
- execution settings should be bounded and inspectable
- artifact hashes should be part of the packaging story from the start

Later phases can add:

- model signatures
- execution policies
- sandboxed subprocess isolation
- audit logs for agent execution

## Non-Goals

- full CPython replacement
- universal Python transpiler
- GPU/provider matrix in MVP
- arbitrary user-supplied ONNX accepted at runtime
- edge/WASM as the first implementation target

## Relationship To Vex

Current recommendation:

- `vex` remains the workflow and developer tool
- `vex-ai-runtime` remains a separate runtime/product exploration
- if the runtime proves out, `vex` can orchestrate it later through templates and commands

That separation keeps both product stories clean.
