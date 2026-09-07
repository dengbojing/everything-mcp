# Everything MCP

通过 MCP 调用本机 Everything 索引，快速查找 Windows 文件和目录。

基于官方 Python MCP SDK，使用 STDIO 协议和 voidtools ES 命令行客户端。提供 **12 个工具**，涵盖精确、关键词、通配符、正则、模糊、拼音和拼写容错搜索。

## 特性

- 返回完整路径、文件大小和修改时间。
- 支持扩展名、大小、修改日期及目录范围过滤。
- 支持全拼、首字母、中文拼音混输和多音字。
- 提供结果分页、索引目录浏览、计数和 IPC 状态检查。
- 没有专门的文件内容搜索、读取或修改工具。

默认搜索 Everything 当前实例的全部索引，不额外设置目录白名单。未被索引的位置不会出现在结果中；搜索结果不代表文件读取权限。通用工具会传递原生 Everything 查询表达式，因此不是限制原生查询能力的安全隔离层。

## 环境要求

| 组件 | 要求 |
| --- | --- |
| 操作系统 | Windows |
| Everything | 已安装并运行，IPC 可访问 |
| ES | 单独安装 es.exe，加入 PATH 或配置绝对路径 |
| Python | 3.11+ |
| uv | 使用 uvx 安装或 uv 开发时需要 |
| Git | 从 GitHub 安装时需要 |

曾在 Python 3.12.8、Everything 1.4.1.1032、ES 1.1.0.37 环境验证。依赖声明见 `pyproject.toml`，锁定版本见 `uv.lock`。

先检查 ES：

```powershell
es -version
es -get-everything-version
es "报告"
```

Everything 桌面程序和 ES 是不同组件，安装前者不一定包含后者。

## 安装

### 从 GitHub 使用 uvx

仓库可访问并已推送项目后：

```powershell
uvx --from "git+https://github.com/dengbojing/everything-mcp.git" everything-mcp
```

首次运行会准备隔离环境，可能下载依赖。STDIO 服务启动后等待输入是正常行为，手动验证时按 Ctrl+C 退出。

可在仓库 URL 后追加 `@提交SHA` 或已发布的标签固定版本。私有仓库需要预先配置 Git 认证，不要把令牌写进 URL 或 MCP 配置。

### 从本地源码运行

```powershell
git clone https://github.com/dengbojing/everything-mcp.git
cd everything-mcp
uv sync
uv run everything-mcp
```

已有本地项目也可直接使用：

```powershell
uvx --from "E:\pyWorkspace\everything-mcp" everything-mcp
```

分发包名为 `everything-es-mcp`，启动入口为 `everything-mcp`。以上方式无需发布到 PyPI。

## 客户端配置

适用于使用 mcpServers JSON 格式的客户端。其他客户端请将相同 command、args、env 填入对应配置项。

### GitHub + uvx

```json
{
  "mcpServers": {
    "everything-es": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/dengbojing/everything-mcp.git",
        "everything-mcp"
      ],
      "env": {
        "EVERYTHING_ES_PATH": "C:\\ProgramData\\chocolatey\\bin\\es.exe"
      }
    }
  }
}
```

请替换 ES 路径。如果 es.exe 已在客户端进程的 PATH 中，可以省略 env。找不到 uvx 时，使用 `Get-Command uvx` 查询其绝对路径。

### 本地虚拟环境

在项目中执行 uv sync 后：

```json
{
  "mcpServers": {
    "everything-es": {
      "command": "E:\\pyWorkspace\\everything-mcp\\.venv\\Scripts\\python.exe",
      "args": ["E:\\pyWorkspace\\everything-mcp\\everything_mcp.py"],
      "env": {
        "EVERYTHING_ES_PATH": "C:\\ProgramData\\chocolatey\\bin\\es.exe"
      }
    }
  }
}
```

配置后重新连接服务，调用 `everything_status`。返回 `connected: true` 才表示成功访问 Everything IPC。

| 环境变量 | 说明 |
| --- | --- |
| EVERYTHING_ES_PATH | es.exe 绝对路径；未设置时从 PATH 查找 |
| EVERYTHING_INSTANCE | Everything 命名实例；未设置时连接默认实例 |
| UV_CACHE_DIR | uv/uvx 缓存位置，由 uv 处理，不改变文件搜索范围 |

## 工具目录

| 工具 | 用途 | 关键参数 |
| --- | --- | --- |
| everything_search | 原生 Everything 表达式 | query、sort、descending、case_sensitive、match_path |
| everything_search_exact | 完整文件名字面匹配，包含扩展名 | name |
| everything_search_keywords | 全部/任一关键词和排除词 | keywords、match、exclude |
| everything_search_wildcard | 完整文件名通配符匹配 | pattern |
| everything_search_regex | 文件名正则匹配 | pattern |
| everything_search_fuzzy | 非连续、连续或无序关键词 | text、mode |
| everything_search_pinyin | 拼音与中文混输 | text、mode、heteronym、candidate_query |
| everything_search_by_type | 扩展名分类 | category、text |
| everything_search_typo | 文件名字符相似度排序 | text、threshold、candidate_query |
| everything_list_directory | 直属或递归索引项 | path、recursive |
| everything_count | 匹配数量 | query、path、kind |
| everything_status | 版本与 IPC 状态 | 无 |

精确搜索指完整名称匹配，默认不区分大小写。需要区分大小写时使用通用搜索的 case_sensitive。

### 通用参数

普通搜索及多数细分工具支持 path、limit、offset。具体以客户端工具 schema 为准。

- path：可选绝对目录路径。
- kind：支持该参数的工具接受 all、file、folder；类型搜索固定为文件。
- limit：默认 50，范围 1–500。
- offset：默认 0，范围 0–100000。
- sort：仅通用搜索暴露，支持 name、path、size、extension、date-created、date-modified，默认 path。
- descending：仅通用搜索暴露，默认 false。

拼音和容错使用候选分页，见下文。

### 过滤条件

十个搜索/目录工具接受 filters；count 和 status 不接受。计数时可在 query 中使用对应 ES 条件。

| filters 字段 | 含义 |
| --- | --- |
| extensions | 扩展名列表，如 ["pdf", "docx"]，最多 30 项 |
| min_bytes / max_bytes | 字节范围，包含边界 |
| modified_from / modified_to | YYYY-MM-DD，包含起止日期当天 |
| recent_days | 含今天在内的本地自然日数量，1–36500 |

recent_days 与显式日期范围互斥。类型搜索中的非空 extensions 会覆盖类别默认列表。

category 支持 document、image、video、audio、code、archive，具体扩展名列表见源码 TYPES。

## 调用示例

以下 JSON 为工具参数，文件名和路径均为示例。

### 精确、关键词、通配符与正则

`everything_search_exact`：

```json
{"name": "年度报告.pdf"}
```

`everything_search_keywords`：

```json
{
  "keywords": ["合同", "2025"],
  "match": "all",
  "exclude": ["草稿"],
  "filters": {"extensions": ["pdf", "docx"]}
}
```

`everything_search_wildcard`：

```json
{"pattern": "报告*2025*.p?f"}
```

只有 * 和 ? 作为通配符，其余字符按字面匹配。

`everything_search_regex`：

```json
{"pattern": "^报告.*202[4-6]\\.pdf$"}
```

### 大文件及日期筛选

`everything_search`：

```json
{
  "query": "file:",
  "filters": {
    "min_bytes": 104857600,
    "modified_from": "2025-01-01",
    "modified_to": "2025-12-31"
  },
  "sort": "size",
  "descending": true,
  "limit": 20
}
```

### 模糊搜索

`everything_search_fuzzy`：

```json
{"text": "年报告", "mode": "subsequence"}
```

| mode | 行为 |
| --- | --- |
| subsequence | 按字符顺序匹配，允许间隔；默认 |
| substring | 连续字面子串 |
| keywords | 按空白拆词，全部命中，顺序不限 |

模糊模式不做拼写纠正，字符容错请使用 typo 工具。

### 拼音搜索

`everything_search_pinyin`：

```json
{
  "text": "年度bg",
  "mode": "mixed",
  "candidate_query": "ext:pdf",
  "candidate_limit": 500
}
```

- full：全拼，例如 niandubaogao。
- initials：首字母，例如 ndbg。
- both：全拼或首字母，默认。
- mixed：中文、全拼及首字母混输。
- heteronym=true：允许单字多读音，可能增加误匹配。

忽略输入中的空格和单引号，ü 规范化为 v；当前不接受数字声调及任意标点。拼音由 pypinyin 转换实现，没有持久化拼音索引。

### 拼写容错

`everything_search_typo`：

```json
{
  "text": "年度报吿",
  "candidate_query": "ext:pdf",
  "threshold": 70
}
```

使用 SequenceMatcher 字符相似度，0–100 分，不是语义检索或编辑距离。输入不含扩展名时比较文件名主体，否则比较完整名称。

### 目录浏览

`everything_list_directory`：

```json
{"path": "D:\\Documents", "recursive": false, "kind": "file"}
```

默认直属索引项，recursive=true 包含子目录内容。这不是直接遍历文件系统。

## 返回结果与分页

普通结果包含 items、returned、offset、has_more、next_offset。每个项目包含 path、size_bytes、date_modified。

拼音和容错先从 ES 获取候选，再在 Python 中匹配：

- candidate_query 默认 file:，建议用扩展名和路径缩小范围。
- candidate_limit 默认 500，最多 500。
- candidate_offset 默认 0，上限 100000。
- 返回 candidates_scanned、candidates_exhausted、next_candidate_offset。
- 保持条件不变，将 next_candidate_offset 传入下一次 candidate_offset。
- 拼音 limit 限制匹配数；容错没有 limit，返回本页全部达标项。

当前页没有结果不代表全部候选都没有结果。容错排名仅在本页有效。索引变化可能影响跨页结果；超出 offset 范围时应缩小条件。

## 开发与测试

```powershell
uv sync --locked
uv run python -m unittest -v
uv run python test_everything.py --integration
```

单元测试覆盖 CSV、空结果、过滤验证、转义、拼音和容错分页。集成测试通过 stdio 初始化、发现工具并调用真实 ES，覆盖搜索、目录、过滤、计数及分页。

当前集成测试含开发机器的固定文件名和元数据断言。在其他机器运行前需要调整样例，并保证 Everything IPC 可访问。

本地源码直接启动可反映修改；uvx 使用独立安装环境。固定提交或标签时，升级需要更新引用并重新连接客户端。

## 常见问题

**找不到 es.exe**：安装 ES，运行 Get-Command es 检查；必要时设置 EVERYTHING_ES_PATH。

**IPC 不可达**：检查 Everything 是否运行、命名实例、Windows 会话和宿主沙箱权限。终端成功不保证受限进程也能访问。服务不会自动提权或重启 Everything，IPC 错误与无匹配结果分别报告。

**GitHub 认证失败**：检查地址、仓库可见性及 Git 凭据。私有仓库应配置 Git 认证，不要使用账号密码或把令牌写入配置。

**uv 缓存权限错误**：设置 UV_CACHE_DIR 为当前用户可写目录。

**启动后等待输入**：STDIO 服务的正常行为。stdout 专用于协议；请通过 MCP 客户端调用 everything_status。

## 实现边界

ES 子进程超时 20 秒，数据库等待参数 10 秒。没有退出 Everything、重建索引、修改设置或导出文件等专用工具，也没有 Everything 1.5 索引日志及持续 watch 功能。

## 参考

- [Everything](https://www.voidtools.com/)
- [ES 命令行文档](https://www.voidtools.com/support/everything/command_line_interface/)
- [Everything 搜索](https://www.voidtools.com/support/everything/searching/)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [pypinyin](https://github.com/mozillazg/python-pinyin)
