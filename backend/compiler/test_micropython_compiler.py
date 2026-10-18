import unittest

from backend.compiler.micropython_compiler import MicroPythonCompiler


class TestMicroPythonCompiler(unittest.TestCase):
    """Tests for the MicroPython bytecode compiler."""

    def setUp(self):
        self.compiler = MicroPythonCompiler()

    def test_compiles_valid_python(self):
        """Valid Python source should produce a non-empty .mpy artifact."""
        source_code = 'print("Hello from WASMBOX compiler test")'

        result = self.compiler.compile(
            source_code=source_code,
            python_version="3.x",
        )

        self.assertEqual(result.status, "COMPILED")
        self.assertIsNotNone(result.artifact)
        self.assertGreater(len(result.artifact), 0)
        self.assertEqual(result.artifact_format, "mpy")

    def test_rejects_empty_source(self):
        """Empty source should return a structured compilation failure."""
        result = self.compiler.compile(
            source_code="",
            python_version="3.x",
        )

        self.assertEqual(result.status, "COMPILATION_FAILED")
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "COMPILATION_ERROR")

    def test_rejects_invalid_python_syntax(self):
        """Invalid Python syntax should not compile successfully."""
        source_code = "def broken(:\n    print('invalid')"

        result = self.compiler.compile(
            source_code=source_code,
            python_version="3.x",
        )

        self.assertEqual(result.status, "COMPILATION_FAILED")
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.code, "COMPILATION_ERROR")


if __name__ == "__main__":
    unittest.main()
