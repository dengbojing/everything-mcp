"""Protect the public tool names and argument fields during refactors."""

import unittest

from everything_mcp.server import create_server

EXPECTED = {
    "everything_search": [
        "query",
        "path",
        "kind",
        "regex",
        "match_path",
        "case_sensitive",
        "sort",
        "descending",
        "limit",
        "offset",
        "filters",
    ],
    "everything_count": ["query", "path", "kind", "regex", "match_path", "case_sensitive"],
    "everything_status": [],
    "everything_search_regex": ["pattern", "path", "kind", "limit", "offset", "filters"],
    "everything_search_fuzzy": ["text", "path", "kind", "limit", "offset", "mode", "filters"],
    "everything_search_pinyin": [
        "text",
        "candidate_query",
        "path",
        "mode",
        "limit",
        "candidate_offset",
        "candidate_limit",
        "heteronym",
        "filters",
    ],
    "everything_search_exact": ["name", "path", "kind", "limit", "offset", "filters"],
    "everything_search_keywords": [
        "keywords",
        "match",
        "exclude",
        "path",
        "kind",
        "limit",
        "offset",
        "filters",
    ],
    "everything_search_wildcard": ["pattern", "path", "kind", "limit", "offset", "filters"],
    "everything_search_by_type": ["category", "text", "path", "limit", "offset", "filters"],
    "everything_list_directory": ["path", "recursive", "kind", "limit", "offset", "filters"],
    "everything_search_typo": [
        "text",
        "candidate_query",
        "path",
        "threshold",
        "candidate_offset",
        "candidate_limit",
        "filters",
    ],
}


class ServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_contract(self):
        tools = await create_server().list_tools()
        self.assertEqual({tool.name for tool in tools}, set(EXPECTED))
        for tool in tools:
            self.assertEqual(set(tool.inputSchema["properties"]), set(EXPECTED[tool.name]))
            self.assertTrue(tool.annotations.readOnlyHint)
