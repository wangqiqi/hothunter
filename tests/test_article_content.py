"""正文提取。"""

from src.utils.article_content import extract_readable_text


def test_extract_paragraphs_from_article_tag() -> None:
    html = """
    <html><body>
      <nav>menu</nav>
      <article>
        <h1>Title</h1>
        <p>这是第一段足够长的正文内容用于测试提取逻辑是否正常工作。</p>
        <p>第二段同样足够长，应该出现在摘要里而不是被过滤掉。</p>
      </article>
    </body></html>
    """
    text = extract_readable_text(html)
    assert "第一段" in text
    assert "第二段" in text
    assert "menu" not in text


def test_extract_fallback_to_paragraphs() -> None:
    html = "<html><body><div><p>没有 article 标签时也应提取这段足够长的段落正文。</p></div></body></html>"
    text = extract_readable_text(html)
    assert "没有 article" in text
