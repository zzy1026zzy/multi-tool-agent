from unittest.mock import Mock

from tools.web_search import WebSearchTool


def mock_search_api(monkeypatch, data):
    monkeypatch.setenv("BOCHA_API_KEY", "test-key")
    monkeypatch.setenv("BOCHA_SEARCH_URL", "https://example.com/search")
    response = Mock()
    response.json.return_value = data
    monkeypatch.setattr("tools.web_search.httpx.post", Mock(return_value=response))
    return response


def test_search_result(monkeypatch):
    response = mock_search_api(monkeypatch, {
        "data": {"webPages": {"value": [{
            "name": "Python 官网",
            "url": "https://python.org",
            "summary": "Python 官方网站",
        }]}}
    })

    result = WebSearchTool().run(query="Python")

    assert "Python 官网" in result
    assert "https://python.org" in result
    assert "Python 官方网站" in result
    response.raise_for_status.assert_called_once()


def test_missing_config(monkeypatch):
    monkeypatch.delenv("BOCHA_API_KEY", raising=False)
    monkeypatch.delenv("BOCHA_SEARCH_URL", raising=False)
    assert "缺少" in WebSearchTool().run(query="新闻")


def test_empty_result(monkeypatch):
    mock_search_api(monkeypatch, {"data": {"webPages": {"value": []}}})
    assert "未找到" in WebSearchTool().run(query="不存在的内容")


def test_schema_shape():
    tool = WebSearchTool()
    schema = tool.openai_schema()
    assert tool.is_available()
    assert schema["function"]["name"] == "web_search"
    assert "query" in schema["function"]["parameters"]["properties"]
