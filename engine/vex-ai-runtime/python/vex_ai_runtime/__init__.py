from __future__ import annotations

from typing import Dict

from vex_ai_runtime.artifacts import ArtifactError, ArtifactManifest, load_artifact_manifest

try:
    from ._core import healthcheck as native_healthcheck
    from ._core import runtime_info as native_runtime_info

    NATIVE_AVAILABLE = True
except ImportError:
    NATIVE_AVAILABLE = False

    def native_healthcheck() -> str:
        return "native-extension-unavailable"

    def native_runtime_info() -> list[tuple[str, str]]:
        return [
            ("name", "vex-ai-runtime"),
            ("engine", "onnxruntime-planned"),
            ("core_language", "rust"),
            ("status", "python-fallback"),
        ]


__all__ = [
    "ArtifactError",
    "ArtifactManifest",
    "NATIVE_AVAILABLE",
    "healthcheck",
    "load_artifact_manifest",
    "runtime_info",
]


def runtime_info() -> Dict[str, str]:
    return dict(native_runtime_info())


def healthcheck() -> str:
    return native_healthcheck()
