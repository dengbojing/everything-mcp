"""Live integration suite; requires Everything and the original sample file."""

import asyncio
import json
import sys


async def integration():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=sys.executable, args=["-m", "everything_mcp"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) == 12

            async def invoke(name, args):
                result = await session.call_tool(name, args)
                assert not result.isError, result
                return json.loads(result.content[0].text)

            status = await invoke("everything_status", {})
            assert status["connected"], status
            cases = [
                ("everything_search", {"query": "人妻约会指南"}),
                ("everything_search_regex", {"pattern": r"人妻.*指南\.pdf$"}),
                ("everything_search_fuzzy", {"text": "人妻指南"}),
                (
                    "everything_search_pinyin",
                    {"text": "renqiyuehuizhinan", "candidate_query": "人妻 ext:pdf"},
                ),
                ("everything_search_pinyin", {"text": "rqyhzn", "candidate_query": "人妻 ext:pdf"}),
                ("everything_search_exact", {"name": "人妻约会指南.pdf"}),
                (
                    "everything_search_keywords",
                    {"keywords": ["人妻", "指南"], "exclude": ["不存在的排除词"]},
                ),
                (
                    "everything_search_keywords",
                    {"keywords": ["人妻约会指南", "不存在的或词"], "match": "any"},
                ),
                ("everything_search_wildcard", {"pattern": "人妻*指南.p?f"}),
                (
                    "everything_search_by_type",
                    {
                        "category": "document",
                        "text": "人妻约会指南",
                        "filters": {
                            "min_bytes": 1000000,
                            "max_bytes": 4000000,
                            "modified_from": "2025-11-01",
                            "modified_to": "2025-11-30",
                        },
                    },
                ),
                ("everything_search_fuzzy", {"text": "指南 人妻", "mode": "keywords"}),
                ("everything_search_fuzzy", {"text": "约会指南", "mode": "substring"}),
                (
                    "everything_search_pinyin",
                    {"text": "人妻yh指南", "mode": "mixed", "candidate_query": "人妻 ext:pdf"},
                ),
                (
                    "everything_search_typo",
                    {"text": "人妻约会指楠", "candidate_query": "人妻 ext:pdf", "threshold": 70},
                ),
            ]
            for name, args in cases:
                data = await invoke(name, args)
                assert any(item["path"].endswith("人妻约会指南.pdf") for item in data["items"]), (
                    data
                )
                print(name, "PASS", data["returned"])
            count = await invoke("everything_count", {"query": "人妻约会指南"})
            import ntpath

            found = await invoke("everything_search_exact", {"name": "人妻约会指南.pdf"})
            parent = ntpath.dirname(found["items"][0]["path"])
            direct = await invoke("everything_list_directory", {"path": parent})
            assert all(
                ntpath.dirname(item["path"]).casefold() == parent.casefold()
                for item in direct["items"]
            )
            excluded = await invoke(
                "everything_search_keywords", {"keywords": ["人妻约会指南"], "exclude": ["指南"]}
            )
            assert excluded["returned"] == 0
            oversize = await invoke(
                "everything_search_exact",
                {"name": "人妻约会指南.pdf", "filters": {"min_bytes": 999999999999}},
            )
            assert oversize["returned"] == 0
            assert count["count"] >= 1
            missing = await invoke("everything_search", {"query": "zz_no_file_85b13f36174c"})
            assert missing["returned"] == 0
            first = await invoke("everything_search", {"query": "ext:pdf", "limit": 1})
            second = await invoke(
                "everything_search", {"query": "ext:pdf", "limit": 1, "offset": 1}
            )
            assert first["has_more"] and first["items"][0]["path"] != second["items"][0]["path"]
            bad = await session.call_tool("everything_search", {"query": "-exit"})
            assert bad.isError
            print("stdio initialize/list/call, count, empty, pagination, rejection PASS")


if __name__ == "__main__":
    asyncio.run(integration())
