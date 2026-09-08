# Everything MCP

通过 MCP 调用 Windows 本机 Everything 索引，查找文件和目录。提供 12 个搜索及辅助工具，支持路径、扩展名、大小和修改日期筛选，返回完整路径及文件元数据。

## 安装准备

需要 Windows、Everything、ES、uv（提供 uvx）及 Git，Python 版本要求为 3.11+。

1. 从 [voidtools 下载页](https://www.voidtools.com/downloads/) 安装 Everything，并保持运行。
2. 在同一页面下载 **Everything Command-line Interface（ES）**，解压到固定目录。
3. 将 **es.exe 所在目录**加入 Windows 用户或系统 PATH，然后重启终端和 MCP 客户端。

Everything 与 ES 是不同组件。如果已安装全局 ES，且客户端能从 PATH 找到它，**无需设置 `EVERYTHING_ES_PATH`**。

验证安装：

```powershell
es -version
es -get-everything-version
es "报告"
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
        "everything-mcp"
      ]
    }
  }
}
```

保存并连接后，调用 `everything_status`，返回 `connected: true` 即连接成功。可在仓库地址后添加已发布的标签或提交 SHA 固定版本。

ES 不在客户端 PATH 中时，才需要在 env 中指定 `EVERYTHING_ES_PATH` 为 es.exe 的绝对路径；命名实例可通过 `EVERYTHING_INSTANCE` 指定。

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
