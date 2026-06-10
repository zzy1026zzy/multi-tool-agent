"""【学生任务】长期记忆：跨会话记住用户事实/偏好，落盘到 JSON。

采用最简单的"关键词召回 / 全量注入"策略（进阶可改向量召回，见 README）。
实现完成后把模块级 ENABLED 改为 True，factory 会自动启用它。
"""
import json
import os

from memory.base import LongTermMemory
from llm import LLMClient

# 实现完成后改为 True
ENABLED = True


class FileLongTermMemory(LongTermMemory):
    def __init__(self, user_id: str = "local", path: str = "data/memory_store.json"):
        self.user_id = user_id
        self.path = path
        self._llm = LLMClient()
        self.facts: list[str] = self._load()

    def _load(self) -> list[str]:
        """从 JSON 文件读取本 user 的事实列表（文件不存在时返回 []）。

        TODO: 读取 self.path，结构建议 {user_id: [fact, ...]}，
        返回 data.get(self.user_id, [])。
        """
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(self.user_id, [])

    def _save(self) -> None:
        """把 self.facts 写回 JSON 文件（保留其它 user 的数据）。

        TODO: 读出整体 dict，更新 self.user_id 对应项，写回文件。
        """
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        data = {}
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)

        data[self.user_id] = self.facts
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def recall(self, query: str) -> list[str]:
        """召回与 query 相关的事实。

        TODO（关键词策略）：返回 query 与事实有词重叠的项；
        事实较少时可直接全量返回。
        """
        if not self.facts:
            return []
        if len(self.facts) <= 10:
            return self.facts
        
        q = query.lower()
        related = []
        for fact in self.facts:
            f = fact.lower()
            if any(word in f for word in q.split() if word.strip()):
                related.append(fact)
        return related[:10]

    def remember(self, user_msg: str, reply: str) -> None:
        """从一轮对话中抽取值得长期记住的事实并落盘。

        TODO:
        1. 用 self._llm.chat() 让模型从对话中抽取"用户的稳定事实/偏好"，
           没有则返回空。
        2. 把新事实去重后加入 self.facts，调用 self._save()。
        """
        # 1. 构造 prompt, 抽取长期事实
        prompt = [
            {
                "role": "system",
                "content": (
                    "你负责从一轮对话中抽取值得长期记住的用户事实和偏好。"
                    "只记录长期稳定的信息，例如姓名、职业、长期偏好、常用语言、项目背景。"
                    "不要记录一次性请求、临时情绪、当前时间、无关闲聊。"
                    "请只返回 JSON 字符串数组；如果没有值得记住的信息，返回 []。"
                ),
            },
            {
                "role": "user",
                "content": f"用户：{user_msg}\n助手：{reply}",
            },
        ]

        # 2. 调用 LLM 抽取事实
        resp = self._llm.chat(prompt)
        content = resp.choices[0].message.content.strip()
        extracted = json.loads(content)

        # 3. 去重加入 self.facts，落盘
        new_facts = [f for f in extracted if f not in self.facts]
        if new_facts:
            self.facts.extend(new_facts)
            self._save()

    def all_facts(self) -> list[str]:
        return list(self.facts)
