"""Build and validate ES search arguments."""

import os
import re

from .models import Kind


def regex_term(pattern: str) -> str:
    if not pattern or len(pattern) > 2048 or any(c in pattern for c in '\x00\r\n"'):
        raise ValueError("pattern must be 1..2048 characters without quotes or line breaks")
    return 'regex:"' + pattern + '"'


def query_args(
    query: str, path: str | None, kind: Kind, regex: bool, match_path: bool, case_sensitive: bool
) -> list[str]:
    if not query.strip() or len(query) > 4096 or any(c in query for c in "\x00\r\n"):
        raise ValueError("query must be nonempty, single-line and at most 4096 characters")
    # ES parses switches itself even with shell=False. Never pass a switch as a query.
    if re.search(r"(?:^|\s)[-/]", query) or query.count('"') % 2:
        raise ValueError(
            "query must not start with an ES switch; use Everything syntax such as regex: or name:"
        )
    if kind not in ("all", "file", "folder"):
        raise ValueError("invalid kind")
    args = [
        "-timeout",
        "10000",
        "-no-case",
        "-no-whole-word",
        "-no-match-path",
        "-no-prefix",
        "-no-suffix",
    ]
    if path:
        if any(c in path for c in '\x00\r\n"') or not os.path.isabs(path):
            raise ValueError(
                "path must be an absolute directory path without quotes or control characters"
            )
        args += ["-path", path]
    if kind != "all":
        args += ["/a-d" if kind == "file" else "/ad"]
    if match_path:
        args += ["-match-path"]
    if case_sensitive:
        args += ["-case"]
    if regex:
        args += ["-regex"]
    return [*args, query]
