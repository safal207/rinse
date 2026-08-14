"""Fail-closed CLI regressions for the RINSE reflection graph."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from rinse.reflection_graph import main


class ReflectionGraphCliFailClosedTests(unittest.TestCase):
    """Verify malformed input is blocked without a Python traceback."""

    def test_invalid_utf8_returns_block_and_exit_two(self) -> None:
        """Invalid UTF-8 must follow the same bounded failure path as bad JSON."""

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.json"
            source.write_bytes(b"\xff\xfe\xfa")
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = main([str(source)])

        self.assertEqual(exit_code, 2)
        self.assertTrue(output.getvalue().startswith("BLOCK: "))
        self.assertNotIn("Traceback", output.getvalue())


if __name__ == "__main__":
    unittest.main()
