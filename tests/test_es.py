"""ES boundary tests without a running Everything instance."""

import subprocess
import unittest
from unittest.mock import patch

from everything_mcp import es


class EsTests(unittest.TestCase):
    @patch.dict(es.os.environ, {"EVERYTHING_ES_PATH": "es.exe"}, clear=True)
    @patch.object(es.subprocess, "run")
    def test_shell_disabled_and_unicode(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, "中文.pdf".encode(), b"")
        self.assertEqual(es.run_es(["-version"]), "中文.pdf")
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertEqual(run.call_args.kwargs["timeout"], 20)

    @patch.dict(es.os.environ, {"EVERYTHING_ES_PATH": "es.exe"}, clear=True)
    @patch.object(es.subprocess, "run")
    def test_timeout(self, run):
        run.side_effect = subprocess.TimeoutExpired("es.exe", 20)
        with self.assertRaisesRegex(RuntimeError, "ES_TIMEOUT"):
            es.run_es(["-version"])

    @patch.dict(es.os.environ, {"EVERYTHING_ES_PATH": "es.exe"}, clear=True)
    @patch.object(es.subprocess, "run")
    def test_ipc_error(self, run):
        run.return_value = subprocess.CompletedProcess(
            [], 8, b"Error 8: Everything IPC not found.", b""
        )
        with self.assertRaisesRegex(RuntimeError, "ES_IPC_UNAVAILABLE"):
            es.run_es(["-get-everything-version"])

    @patch.dict(es.os.environ, {}, clear=True)
    @patch.object(es.shutil, "which", return_value=None)
    def test_missing_executable(self, which):
        with self.assertRaisesRegex(RuntimeError, "ES_NOT_FOUND"):
            es.run_es(["-version"])
