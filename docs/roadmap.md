# Roadmap

## v0.1

- `vex init`
- `vex add`
- `vex remove`
- `vex sync`
- `vex lock`
- `vex run`
- `vex test`
- `vex lint`
- `vex format`
- `vex typecheck`
- `vex doctor`
- `vex python install|pin|list|path|uninstall`
- `vex build`
- `vex publish`
- `vex tool run|install|list|upgrade|uninstall`

## v0.2

- `vex export`
- `vex shell`
- `vex cache`
- basic workspace investigation

## v1 Direction

- polished project templates
- container-oriented deployment helpers
- optional packaging targets like PEX or PyInstaller
- opt-in performance workflows for hot paths

## Product Guardrails

- one project config: `pyproject.toml`
- one default environment: `.venv`
- one core install model: lock then sync
- one clear execution path: `vex run`
- escape hatches are allowed, but secondary
