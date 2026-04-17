from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from vex_ai_runtime import ArtifactError, load_artifact_manifest


class ArtifactTests(unittest.TestCase):
    def test_load_artifact_manifest_accepts_valid_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "models").mkdir()
            (root / "models" / "encoder.onnx").write_bytes(b"fake-model")
            (root / "vex-model.json").write_text(
                json.dumps(
                    {
                        "schema": "vex-model/v1",
                        "schema_version": "v1",
                        "runtime": "vex-ai-runtime",
                        "name": "encoder",
                        "engine": "onnxruntime",
                        "model_path": "models/encoder.onnx",
                        "sha256": "abc123",
                    }
                ),
                encoding="utf-8",
            )

            manifest = load_artifact_manifest(root)

        self.assertEqual(manifest.name, "encoder")
        self.assertEqual(manifest.schema, "vex-model/v1")
        self.assertEqual(manifest.engine, "onnxruntime")
        self.assertEqual(manifest.model_path.name, "encoder.onnx")

    def test_load_artifact_manifest_rejects_parent_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "vex-model.json").write_text(
                json.dumps(
                    {
                        "schema": "vex-model/v1",
                        "schema_version": "v1",
                        "runtime": "vex-ai-runtime",
                        "name": "encoder",
                        "engine": "onnxruntime",
                        "model_path": "../escape.onnx",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ArtifactError):
                load_artifact_manifest(root)

    def test_load_artifact_manifest_requires_known_engine(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "model.onnx").write_bytes(b"fake-model")
            (root / "vex-model.json").write_text(
                json.dumps(
                    {
                        "schema": "vex-model/v1",
                        "schema_version": "v1",
                        "runtime": "vex-ai-runtime",
                        "name": "encoder",
                        "engine": "tract",
                        "model_path": "model.onnx",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ArtifactError):
                load_artifact_manifest(root)

    def test_load_artifact_manifest_requires_schema_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "model.onnx").write_bytes(b"fake-model")
            (root / "vex-model.json").write_text(
                json.dumps(
                    {
                        "name": "encoder",
                        "engine": "onnxruntime",
                        "model_path": "model.onnx",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ArtifactError):
                load_artifact_manifest(root)


if __name__ == "__main__":
    unittest.main()
