"""Everything CLI adapter. stdout belongs exclusively to MCP."""
import csv
import io
import locale
import os
import re
import ntpath
import shutil
import subprocess
from typing import Literal
from datetime import date, timedelta
from pydantic import BaseModel, Field, ConfigDict, model_validator

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

mcp = FastMCP("everything-es")
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
Sort = Literal["name", "path", "size", "extension", "date-created", "date-modified"]
Kind = Literal["all", "file", "folder"]


class Filters(BaseModel):
    """Index metadata only. Dates include the whole calendar day; size is bytes."""
    model_config = ConfigDict(extra="forbid")
    extensions: list[str] = Field(default_factory=list, max_length=30)
    min_bytes: int | None = Field(default=None, ge=0)
    max_bytes: int | None = Field(default=None, ge=0)
    modified_from: date | None = None
    modified_to: date | None = None
    recent_days: int | None = Field(default=None, ge=1, le=36500)

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.min_bytes is not None and self.max_bytes is not None and self.min_bytes > self.max_bytes:
            raise ValueError("min_bytes exceeds max_bytes")
        if self.modified_from and self.modified_to and self.modified_from > self.modified_to:
            raise ValueError("modified_from exceeds modified_to")
        if self.recent_days and (self.modified_from or self.modified_to):
            raise ValueError("use recent_days or a date range, not both")
        for ext in self.extensions:
            if not re.fullmatch(r"\.?[A-Za-z0-9]+", ext):
                raise ValueError("extensions must be plain extensions, e.g. pdf or .docx")
        return self

    def expression(self):
        terms = []
        if self.extensions:
            terms.append("ext:" + ";".join(e.lstrip(".") for e in self.extensions))
        if self.min_bytes is not None:
            terms.append(f"size:>={self.min_bytes}")
        if self.max_bytes is not None:
            terms.append(f"size:<={self.max_bytes}")
        start = date.today() - timedelta(days=self.recent_days - 1) if self.recent_days else self.modified_from
        end = date.today() if self.recent_days else self.modified_to
        if start:
            terms.append(f"dm:>={start.isoformat()}")
        if end:
            terms.append(f"dm:<{(end + timedelta(days=1)).isoformat()}")
        return " ".join(terms)


def regex_term(pattern):
    if not pattern or len(pattern) > 2048 or any(c in pattern for c in '\x00\r\n"'):
        raise ValueError("pattern must be 1..2048 characters without quotes or line breaks")
    return 'regex:"' + pattern + '"'


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
            raise RuntimeError("ES_IPC_UNAVAILABLE: Everything IPC is inaccessible. Check running instance, Windows session and host sandbox permissions; this is not a zero-match result.")
        raise RuntimeError(f"ES_ERROR ({result.returncode}): {details[:2000]}")
    return output


def query_args(query: str, path: str | None, kind: Kind, regex: bool,
               match_path: bool, case_sensitive: bool) -> list[str]:
    if not query.strip() or len(query) > 4096 or any(c in query for c in "\x00\r\n"):
        raise ValueError("query must be nonempty, single-line and at most 4096 characters")
    # ES parses switches itself even with shell=False. Never pass a switch as a query.
    if re.search(r'(?:^|\s)[-/]', query) or query.count('"') % 2:
        raise ValueError("query must not start with an ES switch; use Everything syntax such as regex: or name:")
    if kind not in ("all", "file", "folder"):
        raise ValueError("invalid kind")
    args = ["-timeout", "10000", "-no-case", "-no-whole-word", "-no-match-path", "-no-prefix", "-no-suffix"]
    if path:
        if any(c in path for c in '\x00\r\n"') or not os.path.isabs(path):
            raise ValueError("path must be an absolute directory path without quotes or control characters")
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


@mcp.tool(annotations=READ_ONLY)
def everything_search(query: str, path: str | None = None, kind: Kind = "all",
                      regex: bool = False, match_path: bool = False,
                      case_sensitive: bool = False, sort: Sort = "path",
                      descending: bool = False, limit: int = 50, offset: int = 0,
                      filters: Filters | None = None) -> dict:
    """Search the local Everything index. query supports Everything syntax (ext:pdf, size:>1mb, dm:today). No path means all indexed locations. Returns paths, size bytes and modification times. Pagination reflects a live, changing index. Does not read file contents."""
    if not 1 <= limit <= 500 or not 0 <= offset <= 100000:
        raise ValueError("limit must be 1..500 and offset 0..100000")
    if sort not in ("name", "path", "size", "extension", "date-created", "date-modified"):
        raise ValueError("unsupported sort")
    if filters:
        query = (regex_term(query) if regex else '<' + query + '>') + ' ' + filters.expression()
        regex = False
    query_options = query_args(query, path, kind, regex, match_path, case_sensitive)
    output = run_es(["-csv", "-no-highlight", "-full-path-and-name", "-size", "-date-modified",
                     "-size-format", "1", "-date-format", "1", "-no-digit-grouping",
                     "-sort", sort + ("-descending" if descending else "-ascending"),
                     "-n", str(offset + limit + 1), "-viewport-offset", str(offset),
                     "-viewport-count", str(limit + 1), *query_options], search=True)
    reader = csv.DictReader(io.StringIO(output))
    if reader.fieldnames and "Filename" not in reader.fieldnames:
        raise RuntimeError(f"ES_OUTPUT_FORMAT: expected Filename column, got {reader.fieldnames}")
    rows = list(reader)
    items = [{"path": row["Filename"], "size_bytes": int(row["Size"]) if row.get("Size") else None,
              "date_modified": row.get("Date Modified")} for row in rows[:limit]]
    return {"query": query, "items": items, "returned": len(items), "offset": offset,
            "has_more": len(rows) > limit, "next_offset": offset + limit if len(rows) > limit else None}


@mcp.tool(annotations=READ_ONLY)
def everything_count(query: str, path: str | None = None, kind: Kind = "all",
                     regex: bool = False, match_path: bool = False, case_sensitive: bool = False) -> dict:
    """Count matching indexed files/folders without retrieving their paths."""
    output = run_es(["-get-result-count", "-no-digit-grouping", *query_args(query, path, kind, regex, match_path, case_sensitive)], search=True)
    return {"query": query, "count": int(output.strip())}


@mcp.tool(annotations=READ_ONLY)
def everything_status() -> dict:
    """Check ES version and Everything IPC connectivity. No changes to the service."""
    es_version = run_es(["-version"]).strip()
    try:
        version = run_es(["-get-everything-version"]).strip()
    except RuntimeError as exc:
        return {"connected": False, "es_version": es_version, "error": str(exc)}
    return {"connected": True, "es_version": es_version, "everything_version": version}


@mcp.tool(annotations=READ_ONLY)
def everything_search_regex(pattern: str, path: str | None = None, kind: Kind = "all",
                            limit: int = 50, offset: int = 0, filters: Filters | None = None) -> dict:
    """Search filenames using ES regular expressions, e.g. ^报告.*\\.pdf$."""
    return everything_search(regex_term(pattern), path=path, kind=kind, limit=limit, offset=offset, filters=filters)


@mcp.tool(annotations=READ_ONLY)
def everything_search_fuzzy(text: str, path: str | None = None, kind: Kind = "all",
                            limit: int = 50, offset: int = 0,
                            mode: Literal['subsequence', 'substring', 'keywords'] = 'subsequence',
                            filters: Filters | None = None) -> dict:
    """Filename matching: subsequence (约指南 matches 约会指南), substring, or unordered keywords. Literal characters are escaped; use search_typo for spelling errors."""
    if not text.strip() or len(text) > 128:
        raise ValueError("text must contain 1..128 characters")
    if mode == 'keywords':
        return everything_search_keywords(text.split(), path=path, kind=kind, limit=limit, offset=offset, filters=filters)
    if mode not in ('subsequence', 'substring'):
        raise ValueError('invalid mode')
    pattern = ".*".join(re.escape(c) for c in text.strip()) if mode == 'subsequence' else re.escape(text.strip())
    return everything_search_regex(pattern, path, kind, limit, offset, filters)


@mcp.tool(annotations=READ_ONLY)
def everything_search_pinyin(text: str, candidate_query: str = "file:", path: str | None = None,
                             mode: Literal["full", "initials", "both", "mixed"] = "both",
                             limit: int = 50, candidate_offset: int = 0,
                             candidate_limit: int = 500, heteronym: bool = False,
                             filters: Filters | None = None) -> dict:
    """Match full pinyin, initials or mixed Chinese/pinyin against a bounded ES candidate page. heteronym enables alternative character readings. Continue next_candidate_offset until candidates_exhausted; not an exhaustive global result before that."""
    from pypinyin import lazy_pinyin, Style
    needle = re.sub(r"[\s']+", "", text).lower().replace("ü", "v")
    if not re.fullmatch(r"[a-zv\u3400-\u9fff]{1,128}", needle) or mode not in ("full", "initials", "both", "mixed"):
        raise ValueError("text must be untoned Latin pinyin/initials; mode must be full, initials or both")
    if not 1 <= limit <= 500:
        raise ValueError("limit must be 1..500")
    page = everything_search(candidate_query, path=path, limit=candidate_limit, offset=candidate_offset, filters=filters)
    matches = []
    consumed = 0
    for item in page["items"]:
        consumed += 1
        name = ntpath.basename(item["path"])
        full = "".join(lazy_pinyin(name)).lower()
        initials = "".join(lazy_pinyin(name, style=Style.FIRST_LETTER)).lower()
        matched = ((mode in ("full", "both") and needle in full) or (mode in ("initials", "both") and needle in initials))
        if mode == 'mixed' or heteronym:
            matched = matched or pinyin_match(name, needle, mode, heteronym)
        if matched:
            matches.append({**item, "pinyin": full, "initials": initials, 'match_reason': mode + ' pinyin'})
            if len(matches) == limit:
                break
    more = consumed < len(page["items"]) or page["has_more"]
    return {"items": matches, "returned": len(matches), "candidates_scanned": consumed,
            "candidates_exhausted": not more,
            "next_candidate_offset": candidate_offset + consumed if more else None}


@mcp.tool(annotations=READ_ONLY)
def everything_search_exact(name: str, path: str | None = None, kind: Kind = 'all',
                            limit: int = 50, offset: int = 0, filters: Filters | None = None) -> dict:
    """Match the entire literal basename, including extension. No wildcard interpretation."""
    if not name or ntpath.basename(name) != name:
        raise ValueError('provide a basename, not a path')
    return everything_search_regex('^' + re.escape(name) + '$', path, kind, limit, offset, filters)


@mcp.tool(annotations=READ_ONLY)
def everything_search_keywords(keywords: list[str], match: Literal['all', 'any'] = 'all',
                               exclude: list[str] | None = None, path: str | None = None,
                               kind: Kind = 'all', limit: int = 50, offset: int = 0,
                               filters: Filters | None = None) -> dict:
    """Match all/any literal filename keywords and exclude literal words; words containing spaces remain phrases."""
    if not 1 <= len(keywords) <= 30 or len(exclude or []) > 30 or match not in ('all', 'any'):
        raise ValueError('provide 1..30 keywords and at most 30 exclusions')
    if any(not word.strip() for word in [*keywords, *(exclude or [])]):
        raise ValueError('empty keyword')
    terms = [regex_term(re.escape(word)) for word in keywords]
    expression = '<' + (' ' if match == 'all' else ' | ').join(terms) + '>'
    expression += ''.join(' !' + regex_term(re.escape(word)) for word in exclude or [])
    return everything_search(expression, path=path, kind=kind, limit=limit, offset=offset, filters=filters)


@mcp.tool(annotations=READ_ONLY)
def everything_search_wildcard(pattern: str, path: str | None = None, kind: Kind = 'all',
                               limit: int = 50, offset: int = 0, filters: Filters | None = None) -> dict:
    """Match full basename using * (zero or more characters) and ? (one character). Other characters are literal."""
    if not pattern or len(pattern) > 512:
        raise ValueError('pattern must be 1..512 characters')
    expression = '^' + ''.join('.*' if c == '*' else '.' if c == '?' else re.escape(c) for c in pattern) + '$'
    return everything_search_regex(expression, path, kind, limit, offset, filters)


TYPES = {
    'document': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md', 'csv'],
    'image': ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'tif', 'heic'],
    'video': ['mp4', 'mkv', 'avi', 'mov', 'webm', 'wmv'],
    'audio': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'],
    'code': ['py', 'js', 'ts', 'tsx', 'jsx', 'java', 'go', 'rs', 'c', 'cpp', 'cs', 'sql'],
    'archive': ['zip', '7z', 'rar', 'tar', 'gz'],
}


@mcp.tool(annotations=READ_ONLY)
def everything_search_by_type(category: Literal['document', 'image', 'video', 'audio', 'code', 'archive'],
                               text: str = '', path: str | None = None,
                               limit: int = 50, offset: int = 0, filters: Filters | None = None) -> dict:
    """Search a documented extension category. Explicit filters.extensions overrides the category's default extension list."""
    if category not in TYPES:
        raise ValueError('invalid category')
    selected = filters.model_copy(deep=True) if filters else Filters()
    if not selected.extensions:
        selected.extensions = TYPES[category]
    return everything_search(regex_term(re.escape(text)) if text else 'file:', path=path, kind='file',
                             limit=limit, offset=offset, filters=selected)


@mcp.tool(annotations=READ_ONLY)
def everything_list_directory(path: str, recursive: bool = False, kind: Kind = 'all',
                               limit: int = 50, offset: int = 0, filters: Filters | None = None) -> dict:
    """Browse indexed children (not a filesystem listing). recursive=False returns direct children; missing index entries are not included."""
    if not ntpath.isabs(path) or any(c in path for c in '\x00\r\n"'):
        raise ValueError('absolute directory required')
    query = '*' if recursive else 'parent:"' + ntpath.normpath(path) + '"'
    return everything_search(query, path=path if recursive else None, kind=kind, limit=limit, offset=offset, filters=filters)


@mcp.tool(annotations=READ_ONLY)
def everything_search_typo(text: str, candidate_query: str = 'file:', path: str | None = None,
                           threshold: float = 70, candidate_offset: int = 0,
                           candidate_limit: int = 500, filters: Filters | None = None) -> dict:
    """Rank a bounded page of filenames by SequenceMatcher similarity (0..100). Not semantic search. All matches on the page returned; ranking is page-local. Continue next_candidate_offset for remaining candidates."""
    from difflib import SequenceMatcher
    if not text.strip() or len(text) > 256 or not 0 <= threshold <= 100:
        raise ValueError('nonempty text up to 256 characters and threshold 0..100 required')
    page = everything_search(candidate_query, path=path, limit=candidate_limit, offset=candidate_offset, filters=filters)
    matches = []
    for item in page['items']:
        name = ntpath.basename(item['path'])
        target = name if ntpath.splitext(text)[1] else ntpath.splitext(name)[0]
        score = 100 * SequenceMatcher(None, text.casefold(), target.casefold(), autojunk=False).ratio()
        if score >= threshold:
            matches.append({**item, 'score': round(score, 2), 'match_reason': 'filename similarity'})
    matches.sort(key=lambda item: (-item['score'], item['path']))
    return {'items': matches, 'returned': len(matches), 'candidates_scanned': len(page['items']),
            'candidates_exhausted': not page['has_more'], 'next_candidate_offset': page['next_offset'],
            'ranking_scope': 'candidate_page'}


def pinyin_match(name, needle, mode, heteronym):
    """Bounded dynamic matching; no exponential polyphonic combinations."""
    from pypinyin import pinyin, Style
    readings = ([pinyin(char, style=Style.NORMAL, heteronym=True)[0] for char in name]
                if heteronym else pinyin(name, style=Style.NORMAL, errors=lambda chars: list(chars)))
    states = {0}
    for char, sounds in zip(name, readings):
        choices = set()
        if mode in ('full', 'both', 'mixed'):
            choices.update(sounds)
        if mode in ('initials', 'both', 'mixed'):
            choices.update(s[0] for s in sounds if s)
        if mode == 'mixed':
            choices.add(char)
        next_states = {0}
        for index in states:
            for choice in choices:
                if needle.startswith(choice.lower(), index):
                    end = index + len(choice)
                    if end == len(needle):
                        return True
                    next_states.add(end)
        states = next_states
    return False


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
