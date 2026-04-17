from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


MANIFEST_FILENAME = "vex-model.json"
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "vex-model-schema.json"


class ArtifactError(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactManifest:
    schema: str
    schema_version: str
    runtime: str
    name: str
    engine: str
    model_path: Path
    sha256: str | None = None


def load_schema() -> dict[str, str]:
    default = {
        "schema": "vex-model/v1",
        "schema_version": "v1",
        "runtime": "vex-ai-runtime",
        "engine": "onnxruntime",
    }
    if not SCHEMA_PATH.exists():
        return default
    try:
        data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default
    if not isinstance(data, dict):
        return default
    merged = dict(default)
    merged.update({k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)})
    return merged


def _safe_relative_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        raise ArtifactError("model_path must be relative")
    if any(part == ".." for part in path.parts):
        raise ArtifactError("model_path must not escape the artifact directory")
    return path


def load_artifact_manifest(root: str | Path) -> ArtifactManifest:
    root_path = Path(root).resolve()
    manifest_path = root_path / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise ArtifactError(f"missing {MANIFEST_FILENAME}")

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ArtifactError(f"invalid manifest JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ArtifactError("manifest must be a JSON object")

    name = data.get("name")
    schema = data.get("schema")
    schema_version = data.get("schema_version")
    runtime = data.get("runtime")
    engine = data.get("engine")
    model_path_raw = data.get("model_path")
    sha256 = data.get("sha256")
    shared = load_schema()

    if schema != shared["schema"]:
        raise ArtifactError(f"manifest field 'schema' must be '{shared['schema']}'")
    if schema_version != shared["schema_version"]:
        raise ArtifactError(f"manifest field 'schema_version' must be '{shared['schema_version']}'")
    if runtime != shared["runtime"]:
        raise ArtifactError(f"manifest field 'runtime' must be '{shared['runtime']}'")

    if not isinstance(name, str) or not name.strip():
        raise ArtifactError("manifest field 'name' must be a non-empty string")
    if engine != shared["engine"]:
        raise ArtifactError(f"manifest field 'engine' must be '{shared['engine']}' for MVP")
    if not isinstance(model_path_raw, str) or not model_path_raw.strip():
        raise ArtifactError("manifest field 'model_path' must be a non-empty string")
    if sha256 is not None and not isinstance(sha256, str):
        raise ArtifactError("manifest field 'sha256' must be a string when present")

    model_rel = _safe_relative_path(model_path_raw)
    model_path = root_path / model_rel
    if not model_path.is_file():
        raise ArtifactError(f"model file not found: {model_rel}")

    return ArtifactManifest(
        schema=schema,
        schema_version=schema_version,
        runtime=runtime,
        name=name.strip(),
        engine=engine,
        model_path=model_path,
        sha256=sha256,
    )
