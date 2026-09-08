"""MCP tool registration and STDIO entry point."""

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import service


def create_server() -> FastMCP:
    """Create an independent server with the stable public tool contract."""
    server = FastMCP("everything-es")
    annotations = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
    for tool in (
        service.everything_search,
        service.everything_count,
        service.everything_status,
        service.everything_search_regex,
        service.everything_search_fuzzy,
        service.everything_search_pinyin,
        service.everything_search_exact,
        service.everything_search_keywords,
        service.everything_search_wildcard,
        service.everything_search_by_type,
        service.everything_list_directory,
        service.everything_search_typo,
    ):
        server.add_tool(tool, annotations=annotations)
    return server


def main() -> None:
    create_server().run(transport="stdio")
