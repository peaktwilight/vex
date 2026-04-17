from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from vex_ai_runtime import NATIVE_AVAILABLE, healthcheck, runtime_info


class PackageTests(unittest.TestCase):
    def test_runtime_info_has_expected_shape(self) -> None:
        info = runtime_info()
        self.assertEqual(info["name"], "vex-ai-runtime")
        self.assertEqual(info["core_language"], "rust")

    def test_healthcheck_reports_status(self) -> None:
        value = healthcheck()
        self.assertIn(value, {"ok", "native-extension-unavailable"})

    def test_native_flag_is_boolean(self) -> None:
        self.assertIsInstance(NATIVE_AVAILABLE, bool)


if __name__ == "__main__":
    unittest.main()
