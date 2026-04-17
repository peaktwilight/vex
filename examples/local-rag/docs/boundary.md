# Product Boundary

vex owns the AI application workflow. It does not try to beat `uv` at
dependency installation, virtualenvs, Python version management, lockfiles, or
generic Python workspace handling.

## What vex owns

- AI project scaffolding (`vex init agent`, `vex init inference-api`)
- local development loops for agents and inference APIs
- runtime selection and switching
- benchmarking and evaluation entry points
- policy and sandbox defaults
- model packaging orchestration
- promotion to deployment targets

## What vex-ai-runtime owns

- native model artifact loading
- runtime session creation
- secure packaged artifact validation
- cold-start and packaged-runtime optimization

## Integrations

vex integrates rather than replaces: `uv` for package and env management,
`ollama` for a local model runtime, agent frameworks like `PydanticAI`, eval
tools like `promptfoo` or `deepeval`, and deployment targets like Modal,
BentoML, Baseten, or custom containers.
