"""词频分析单元测试。"""

from src.analysis.word_freq import analyze_titles, extract_words


def test_extract_words_filters_stopwords():
    words = extract_words("人工智能的大模型发布了")
    assert "人工智能" in words
    assert "大模型" in words
    assert "的" not in words


def test_analyze_titles_excludes_keyword():
    titles = ["AI大模型发布", "大模型算力提升", "AI芯片突破"]
    result = analyze_titles(titles, keyword="AI")
    words = dict(result)
    assert "AI" not in words
    assert "大模型发布" in words or "芯片突破" in words
