# 平台覆盖清单

## 内置必接（12 源）

| ID | 名称 | 实时流热榜 | 定制模式 | 说明 |
|----|------|:----------:|:--------:|------|
| `weibo` | 微博热搜 | ✅ | ✅ | 官方 side/hotSearch |
| `zhihu` | 知乎热榜 | ✅ | ✅ | hot-list-web API |
| `baidu_hot` | 百度热搜 | ✅ | ✅ | top.baidu.com 榜单 |
| `douyin` | 抖音热榜 | ✅ | ✅ | 抖音 web 热词接口 |
| `toutiao` | 今日头条 | ✅ | ✅ | 热榜 API |
| `bilibili` | B站热门 | ✅ | ✅ | 综合热门视频 |
| `tencent` | 腾讯新闻 | ✅ | ✅ | 新闻热榜 |
| `netease` | 网易热点 | ✅ | ✅ | 网易热文 JSONP |
| `tieba` | 贴吧热议 | ✅ | ✅ | 热议话题页（网络差时可能超时） |
| `36kr` | 36氪 | ✅ | ✅ | 科技创投热榜 |
| `baidu` | 百度新闻 | ❌ | ✅ | **新闻搜索**，非热搜榜 |
| `xiaohongshu` | 小红书 | ❌ | ✅ | 无公开热榜；定制模式为搜索入口 |

## 仍未内置（可自建源接入）

微信热搜 / 视频号、快手热榜、澎湃/新浪门户、虎扑、NGA 等 — 见 [CUSTOM_SOURCES.md](CUSTOM_SOURCES.md)。

## 自定义源

复制仓库根目录 `sources.example.json` → `~/.hothunter/sources.json`，按 JSON / RSS 声明即可，**无需改代码**。修改后需重启 App。
