# Everything ES MCP

## 扩展搜索（当前版本）

新增六个工具：everything_search_exact、everything_search_keywords、everything_search_wildcard、everything_search_by_type、everything_list_directory、everything_search_typo。目前共十二个工具。

- exact：完整文件名含扩展名的字面匹配。
- keywords：match=all/any，并支持 exclude；输入词按字面匹配。
- wildcard：完整文件名匹配，只有 * 和 ? 是通配符。
- by_type：document/image/video/audio/code/archive；具体扩展名集合见代码 TYPES。filters.extensions 可覆盖集合。
- list_directory：默认直属子项，recursive=true 递归；结果来自索引，非文件系统完整枚举。
- typo：SequenceMatcher 字符相似度，threshold=0..100；按本页分数排序，非语义匹配。返回本页全部达标结果，按 next_candidate_offset 继续。
- fuzzy：mode=subsequence/substring/keywords，默认保留顺序子序列行为。
- pinyin：mode=full/initials/both/mixed；mixed 允许“人妻yh指南”等混输；heteronym=true 按单字枚举读音，可能增加误匹配。动态匹配避免枚举指数级组合。没有新增持久化拼音缓存。

搜索工具支持 filters 对象：extensions、min_bytes、max_bytes、modified_from、modified_to、recent_days。日期为 YYYY-MM-DD，起止日期包含当天；recent_days 表示含今天在内的本地自然日，与显式日期范围互斥。字节范围包含边界。大文件搜索可使用 everything_search(query="file:", filters={"min_bytes":104857600}, sort="size", descending=true)。时间和大小不增加独立工具。

示例参数：

```json
{"keywords":["合同","2025"],"exclude":["草稿"],"filters":{"extensions":["pdf","docx"],"modified_from":"2025-01-01","modified_to":"2025-12-31"}}
```

拼音与容错都是有界候选匹配：当前页零匹配不等于全盘不存在；分页过程中索引变化可能影响结果。所有新增功能仅使用文件名和索引元数据，不读取文件内容。

Windows 本地只读 MCP，基于官方 Python MCP SDK，使用 stdio 调用 ES。

## 工具

| 工具 | 行为 |
| --- | --- |
| everything_search | Everything 原生表达式；关键词、通配符、ext:pdf、size:>1mb、dm:today；可按路径、类型、排序和分页筛选 |
| everything_search_regex | 正则匹配文件名，如 `人妻.*指南\.pdf$` |
| everything_search_fuzzy | 字符按顺序非连续匹配，如 `人妻指南`；不是错别字或编辑距离匹配 |
| everything_search_pinyin | 全拼 `renqiyuehuizhinan` 或首字母 `rqyhzn`；Python pypinyin 转换候选文件名 |
| everything_count | 查询结果数 |
| everything_status | ES 版本、Everything 版本、IPC 状态 |

拼音搜索用 candidate_query（例如 ext:pdf）和 path 缩小 ES 候选范围。每次最多检查 500 个候选，按 next_candidate_offset 继续；只有 candidates_exhausted=true 才表示候选查完。使用词组默认读音，不枚举所有多音字。普通搜索默认覆盖 Everything 全部索引，不增加目录白名单。搜索结果不代表文件读取权限。

## 环境与启动

本机 Python 3.12.8；隔离环境锁定版本见 uv.lock。Everything 必须已运行，ES 必须在 PATH，或设置 EVERYTHING_ES_PATH。可用 EVERYTHING_INSTANCE 选择命名实例。

```powershell
cd E:\pyWorkspace\everything-mcp
uv sync --cache-dir .uv-cache
.\.venv\Scripts\python.exe -m everything_mcp
```

MCP 客户端通用 JSON 配置（未自动修改宿主配置）：

```json
{
  "mcpServers": {
    "everything-es": {
      "command": "E:\\pyWorkspace\\everything-mcp\\.venv\\Scripts\\python.exe",
      "args": ["E:\\pyWorkspace\\everything-mcp\\everything_mcp.py"],
      "env": {"EVERYTHING_ES_PATH": "C:\\ProgramData\\chocolatey\\bin\\es.exe"}
    }
  }
}
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe test_everything.py --integration
```

联调使用本机已知文件“人妻约会指南.pdf”，测试 stdio 初始化、列举六个工具、中文/正则/模糊/全拼/首字母搜索、计数、空结果、分页和危险开关拒绝。换机器时需替换该样例。

ES 进程设置 20 秒超时；错误通过 MCP 返回。IPC 不可达时检查宿主 Windows 会话和沙箱审批，不自动提权、不启动或重启 Everything。stdout 专用于协议。使用 shell=False，不提供任意 ES 开关入口，不暴露退出、重建索引、修改设置、导出文件操作。查询拒绝控制字符、不平衡引号以及空白后以 - 或 / 开头的开关式词项。

已发现 ES 1.1.0.37 不接受 -no-regex，因此未使用该选项。ES 1.5 索引日志、watch 等功能暂未提供。

## 参考

- https://www.voidtools.com/support/everything/command_line_interface/
- https://github.com/modelcontextprotocol/python-sdk/tree/v1.x
- https://github.com/mozillazg/python-pinyin
