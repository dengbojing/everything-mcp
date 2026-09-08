"""Execute the local ES process without a shell."""

import locale
import os
import shutil
import subprocess


def run_es(args: list[str], search: bool = False) -> str:
    executable = os.environ.get("EVERYTHING_ES_PATH") or shutil.which("es.exe")
    if not executable:
        raise RuntimeError("ES_NOT_FOUND: install voidtools ES or set EVERYTHING_ES_PATH")
    instance = os.environ.get("EVERYTHING_INSTANCE")
    command = [executable, *(["-instance", instance] if instance else []), *args]
    # ES consumes a Windows search expression. list2cmdline would quote the
    # entire expression containing spaces, changing AND terms into a phrase.
    if search:
        command = subprocess.list2cmdline(command[:-1]) + " " + command[-1]
    try:
        result = subprocess.run(command, capture_output=True, timeout=20, shell=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ES_TIMEOUT: Everything did not respond within 20 seconds") from exc
    except OSError as exc:
        raise RuntimeError(f"ES_START_FAILED: {exc}") from exc

    def decode(raw: bytes) -> str:
        try:
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return raw.decode(locale.getpreferredencoding(False), errors="strict")

    output, error = decode(result.stdout), decode(result.stderr)
    if result.returncode:
        details = (error or output).strip()
        if "IPC not found" in details:
            raise RuntimeError(
                "ES_IPC_UNAVAILABLE: Everything IPC is inaccessible. Check running instance, Windows session and host sandbox permissions; this is not a zero-match result."
            )
        raise RuntimeError(f"ES_ERROR ({result.returncode}): {details[:2000]}")
    return output
