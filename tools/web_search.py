"""【学生任务】网络搜索工具。

教学提示：可以接真实搜索 API，也可以先用 mock 数据跑通流程
（与 weather.py 同理）。完成 run() 后把 is_available() 改为 True。
"""
from tools.base import Tool
import os
import httpx

class WebSearchTool(Tool):
    name = "web_search"
    description = (
        "根据用户的问题进行联网搜索，返回网页标题、摘要和链接。"
        "当用户询问最新消息、新闻、实时信息、网络资料、近期事件、公开网页内容时调用。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"}
        },
        "required": ["query"],
    }

    def is_available(self) -> bool:
        # TODO: 实现 run() 后改为 return True
        return True

    def run(self, query: str) -> str:
        """执行搜索并返回结果摘要字符串。

        TODO: 调用真实搜索 API，或先返回 mock 结果跑通链路。
        """
        # 设置API
        api_key = os.getenv("BOCHA_API_KEY")
        url = os.getenv("BOCHA_SEARCH_URL")
        if not api_key or not url:
            return "缺少 BOCHA_API_KEY 或 BOCHA_SEARCH_URL，无法执行搜索。"

        # 构造请求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "summary": True,
            "count": 5,
        }

        response = httpx.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()

        # 解析结果
        data = response.json()
        search_data = data.get("data", {})
        items = search_data.get("webPages", {}).get("value", [])
        if not items:
            return "未找到相关搜索结果。"
        results = []
        for item in items:
            results.append(
                f"标题：{item.get('name', '')}\n"
                f"链接：{item.get('url', '')}\n"
                f"摘要：{item.get('summary') or item.get('snippet') or ''}"
            )
        return "\n\n".join(results)


