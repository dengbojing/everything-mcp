# evryth-mcp

English | [简体中文](README.md)

Search files and directories in your local Windows Everything index through MCP.
Provides 12 search and utility tools, with filters for path, extension, size, and
modification date. Results include full paths and file metadata.

## Prerequisites

The current version runs only on Windows and requires local Everything and ES
installations. Native execution on macOS, Linux, and other Unix-like systems is
not currently supported.

Install Everything, ES, and uv (which provides uvx). Python 3.11+ is required.
Installation uses PyPI; Git and a repository clone are not required.

1. Install Everything from the [voidtools downloads page](https://www.voidtools.com/downloads/) and keep it running.
2. Download **Everything Command-line Interface (ES)** from the same page and extract it to a permanent directory.
3. Add the **directory containing es.exe** to your Windows user or system PATH, then restart your terminal and MCP client.

Everything and ES are separate components. If ES is already installed globally
and your client can find it on PATH, **you do not need `EVERYTHING_ES_PATH`**.

Verify the installation:

```powershell
es -version
```

## MCP configuration

Use `uvx evryth-mcp` to automatically install from [PyPI](https://pypi.org/project/evryth-mcp/)
and start the server. No separate `pip install` step is needed.

For clients using the `mcpServers` JSON configuration format:

```json
{
  "mcpServers": {
    "everything-es": {
      "command": "uvx",
      "args": ["evryth-mcp"]
    }
  }
}
```

After connecting, call `everything_status` and confirm that it returns
`connected: true`.

If ES is on your client's PATH and you use the default Everything instance,
the configuration above is sufficient; no environment variables are needed.

To specify an ES path or a named instance, add `env` to `everything-es`:

```json
{
  "mcpServers": {
    "everything-es": {
      "command": "uvx",
      "args": ["evryth-mcp"],
      "env": {
        "EVERYTHING_ES_PATH": "D:\\Tools\\Everything\\es.exe",
        "EVERYTHING_INSTANCE": "Work"
      }
    }
  }
}
```

- `EVERYTHING_ES_PATH`: Replace with the actual absolute path to `es.exe`, not `Everything.exe` or a directory. Omit this variable if the client can find ES on PATH.
- `EVERYTHING_INSTANCE`: The name of an already-running Everything instance, such as `Work`. Omit it for the default instance. This setting does not create or start an instance.

These variables can be used independently. Remove the entire `env` object if
neither is needed.

## Tools

| Tool | Purpose |
| --- | --- |
| everything_search | Native Everything queries, sorting, and pagination |
| everything_search_exact | Exact full filename matching |
| everything_search_keywords | All/any keywords and exclusions |
| everything_search_wildcard | * and ? wildcards |
| everything_search_regex | Regular expressions |
| everything_search_fuzzy | Contiguous, non-contiguous, and unordered keyword matching |
| everything_search_pinyin | Full pinyin, initials, mixed Chinese/pinyin, and polyphonic characters |
| everything_search_by_type | Documents, images, videos, audio, code, and archives |
| everything_search_typo | Filename character-similarity matching |
| everything_list_directory | Direct or recursive directory index entries |
| everything_count | Match counts |
| everything_status | Versions and IPC status |

For example, ask your client to find PDFs containing “contract” and “2025” but
excluding “draft”, or search for 年度报告 using the pinyin `niandubaogao`.
Detailed parameters are available in the client's tool descriptions.

## Usage notes

- Searches the entire Everything index by default, without additional directory restrictions. Unindexed files will not appear.
- No dedicated file-content search or file-modification tools are provided.
- Pinyin and typo matching operate on candidate pages. An empty page does not mean there are no matches across the index; typo similarity ranking is limited to the current page.
- If IPC is inaccessible, check that Everything is running and review the client's session and sandbox permissions.
- If ES works in a terminal but the client cannot find it, fully restart the client so it inherits the updated PATH.

[Official ES documentation](https://www.voidtools.com/support/everything/command_line_interface/)
