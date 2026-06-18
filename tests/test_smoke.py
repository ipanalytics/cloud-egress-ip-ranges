from __future__ import annotations

import subprocess
import sys
import unittest

import cloud_egress_ip_ranges


class SmokeTests(unittest.TestCase):
    def test_version_is_available(self) -> None:
        self.assertRegex(cloud_egress_ip_ranges.__version__, r"^\d+\.\d+\.\d+$")

    def test_module_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "cloud_egress_ip_ranges", "--help"],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("cloud-egress-ip-ranges", result.stdout)


if __name__ == "__main__":
    unittest.main()

