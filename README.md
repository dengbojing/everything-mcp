# evryth-mcp

通过 MCP 调用 Windows 本机 Everything 索引，查找文件和目录。提供 12 个搜索及辅助工具，支持路径、扩展名、大小和修改日期筛选，返回完整路径及文件元数据。

## 安装准备

当前版本仅支持在 Windows 上运行，依赖本机 Everything 和 ES；macOS、Linux 及其他 Unix 类系统暂不支持原生运行。

需安装 Everything、ES、uv（提供 uvx）及 Git，Python 版本要求为 3.11+。

1. 从 [voidtools 下载页](https://www.voidtools.com/downloads/) 安装 Everything，并保持运行。
2. 在同一页面下载 **Everything Command-line Interface（ES）**，解压到固定目录。
3. 将 **es.exe 所在目录**加入 Windows 用户或系统 PATH，然后重启终端和 MCP 客户端。

Everything 与 ES 是不同组件。如果已安装全局 ES，且客户端能从 PATH 找到它，**无需设置 `EVERYTHING_ES_PATH`**。

验证安装：

```powershell
es -version
```

## MCP 配置

适用于使用 `mcpServers` JSON 格式的客户端：

```json
{
  "mcpServers": {
    "everything-es": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/dengbojing/everything-mcp.git",
        "evryth-mcp"
      ]
    }
  }
}
```

以上 GitHub 配置需要仓库已包含新的启动入口。发布到 PyPI 后，可将 `args` 简化为 `["evryth-mcp"]`，即 `uvx evryth-mcp`，届时无需 Git。

如果 ES 已在客户端 PATH 中且使用默认 Everything 实例，上面的配置即可，无需添加环境变量。

需要指定 ES 路径或命名实例时，在 `everything-es` 配置中添加 `env`：

```json
{
  "mcpServers": {
    "everything-es": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/dengbojing/everything-mcp.git",
        "evryth-mcp"
      ],
      "env": {
        "EVERYTHING_ES_PATH": "D:\\Tools\\Everything\\es.exe",
        "EVERYTHING_INSTANCE": "Work"
      }
    }
  }
}
```

- `EVERYTHING_ES_PATH`：替换为实际 `es.exe` 的绝对路径，不是 `Everything.exe` 或目录；客户端能从 PATH 找到 ES 时可删除此项。
- `EVERYTHING_INSTANCE`：填写已运行的 Everything 命名实例名称，示例为 `Work`；使用默认实例时删除此项。它不会自动创建或启动实例。

这两项可独立使用；如果都不需要，删除整个 `env`。

## 工具

| 工具 | 功能 |
| --- | --- |
| everything_search | Everything 原生查询、排序和分页 |
| everything_search_exact | 完整文件名匹配 |
| everything_search_keywords | 全部/任一关键词及排除词 |
| everything_search_wildcard | * 和 ? 通配符 |
| everything_search_regex | 正则表达式 |
| everything_search_fuzzy | 连续、非连续及无序关键词匹配 |
| everything_search_pinyin | 全拼、首字母、中文混输及多音字 |
| everything_search_by_type | 文档、图片、视频、音频、代码、压缩包 |
| everything_search_typo | 文件名字符相似度匹配 |
| everything_list_directory | 直属或递归目录索引项 |
| everything_count | 匹配数量 |
| everything_status | 版本与 IPC 状态 |

例如，让客户端“查找包含合同和2025、排除草稿的 PDF”，或“按拼音 niandubaogao 搜索年度报告”。具体参数由客户端工具描述提供。

## 使用说明

- 默认搜索 Everything 全部索引，不额外限制目录；未索引的文件不会出现。
- 没有专门的文件内容搜索或文件修改工具。
- 拼音和容错按候选分页匹配，单页无结果不代表全盘不存在；容错分数仅在当前页排序。
- IPC 不可达时，检查 Everything 是否运行，以及客户端会话和沙箱权限。
- 终端能执行 ES 而客户端找不到时，先完全重启客户端，使其继承最新 PATH。

[ES 官方文档](https://www.voidtools.com/support/everything/command_line_interface/)
