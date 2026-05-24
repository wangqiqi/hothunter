# 热点猎手 (Hotspot Hunter) 设计规范

**版本**: v0.1.0  
**日期**: 2026-05-24  
**定位**: 基于 Flet + Python 的纯本地移动端热点抓取与分析工具

---

## 1. 核心功能

- 双模式抓取：
  - **实时流热点**：各平台原生热榜，全量展示，无需关键词
  - **定制热点**：按关键词过滤热榜 / 百度搜索
- 多平台（知乎、36氪、B站、微博、头条 + 定制模式下的百度新闻）
- 关键词过滤 + 本地 SQLite 持久化
- 卡片式结果展示 + 点击跳转
- 中文热词分析（正则分词 + 词频 Top10）
- 历史记录查看

**非功能**：离线优先、<100MB 内存、Android/iOS 支持、反爬延时

---

## 2. 架构概览

```
Flet UI (Column/Row + 卡片)
    ↓
控制逻辑 (事件处理、抓取协调)
    ├── 爬虫模块 (统一接口 + 4平台实现)
    ├── 存储模块 (SQLite CRUD)
    └── 分析模块 (中文词频统计)
```

---

## 3. 模块设计

### 3.1 UI 模块
- TextField（关键词，默认 "AI"）
- CheckboxGroup（平台多选）
- ElevatedButton（抓取 / 历史）
- 状态 Text + 滚动结果 Column + 分析 Column

### 3.2 爬虫模块
统一返回：
```python
{"title": str, "platform": str, "url": str, "hot_value": str, "publish_time": str, "content_snippet": str}
```
平台：知乎 CSS、36氪 JSON、B站 API、百度搜索页

反爬：fake_useragent + sleep(1)

### 3.3 存储模块
表 `articles`（id, title, platform, url, hot_value, publish_time, content_snippet, keyword, fetch_time）
索引：keyword + fetch_time

API：save_articles, get_history, get_titles_by_keyword

### 3.4 分析模块
正则 `[\u4e00-\u9fa5]{2,}` 提取中文词 → 过滤停用词/关键词 → Counter Top10

---

## 4. 数据流

**实时流**：选平台 → 抓取热榜（不过滤）→ 存 `keyword=__stream__` → 展示 + 全站词频  
**定制**：输入关键词 → 抓取并过滤 → 存用户关键词 → 展示 + 排除关键词的词频  
历史：按当前模式对应的 storage key 查询

---

## 5. 扩展点
- 新平台只需实现 fetch 函数并注册
- 定时抓取、导出 CSV、热度数值排序

---

## 6. 部署
Flet App + 脚本文件 → 手机运行 → Wi-Fi 下使用

---

*本规范基于用户原型精简整理，保留核心，去除冗余 ASCII 和重复描述。*