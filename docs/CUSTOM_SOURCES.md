# 自定义媒体源

热点猎手**支持在不改代码的情况下**增加媒体来源，配置写在：

`~/.hothunter/sources.json`

修改后请 **重启 App**（`./scripts/onekey_start.sh restart`）。

## 快速开始

```bash
mkdir -p ~/.hothunter
cp sources.example.json ~/.hothunter/sources.json
# 编辑 enabled: true 并填写真实 URL
```

## JSON 热榜 API（type: `json`）

```json
{
  "sources": [
    {
      "id": "company_hot",
      "name": "公司热榜",
      "icon": "司",
      "enabled": true,
      "type": "json",
      "url": "https://api.example.com/v1/hot",
      "method": "GET",
      "referer": "https://example.com",
      "items_path": "data.items",
      "title_field": "title",
      "url_field": "link",
      "hot_field": "score",
      "stream": true
    }
  ]
}
```

| 字段 | 说明 |
|------|------|
| `id` | 唯一标识（字母数字下划线） |
| `name` | 界面显示名（会自动加「自定义」后缀） |
| `items_path` | 列表在 JSON 中的路径，如 `data.list` |
| `title_field` / `url_field` | 条目中标题、链接字段名 |
| `hot_field` | 可选，热度字段 |
| `stream` | `false` 时仅「定制热点」模式可用（等同搜索型源） |
| `method` | `GET`（默认）或 `POST`（需配 `body`） |

## RSS（type: `rss`）

```json
{
  "id": "my_rss",
  "name": "行业 RSS",
  "icon": "R",
  "enabled": true,
  "type": "rss",
  "url": "https://example.com/feed.xml",
  "stream": true
}
```

## 代码扩展（高级）

若需复杂登录、签名、解析逻辑，可在 `src/crawler/` 新增模块，并在 `src/crawler/registry.py` 的 `BUILTIN_CRAWLERS` 注册。自定义 JSON/RSS 已覆盖大多数内部 API / 聚合场景。

## 限制

- 仅支持 **GET/POST JSON** 与 **RSS 2.0**，无 JavaScript 渲染。
- 请遵守目标站点的服务条款与 robots 规则。
- 自定义源与内置源一样受 `REQUEST_DELAY_SEC` 限速。
