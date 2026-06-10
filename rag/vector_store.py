"""【学生任务】内存向量库：用 numpy 实现最简单的余弦相似度检索。

实现要点：
- add(texts, embeddings): 把文本块和对应向量存起来。
- search(query_embedding, top_k): 返回相似度最高的 top_k 个块。
- 用模块级共享实例 STORE，让 ingest.py 入库、knowledge_base.py 检索
  访问的是同一个库。

完成 search()/add() 后，本文件无需额外开关；让 knowledge_base.py
的 is_available() 返回 True 即可启用 RAG。
"""
import numpy as np


class VectorStore:
    def __init__(self):
        self.texts: list[str] = []
        self.embeddings: list[list[float]] = []
        self.metadatas: list[dict] = []

    def __len__(self) -> int:
        return len(self.texts)

    def add(self, texts: list[str], embeddings: list[list[float]], metadatas: list[dict] | None = None) -> None:
        """把若干文本块及其向量加入库中。

        TODO: 追加到 self.texts / self.embeddings / self.metadatas。
        metadatas 为 None 时用空 dict 占位，长度需与 texts 对齐。
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]      # 没给来源就用空 dict 占位，长度要和 texts 对齐
        self.texts.extend(texts)                 # 三个列表同步追加，靠相同下标对应同一个块
        self.embeddings.extend(embeddings)
        self.metadatas.extend(metadatas)

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[dict]:
        """检索最相似的 top_k 个块。

        返回: [{"text": str, "score": float, "metadata": dict}, ...]，按 score 降序。

        TODO:
        1. 库为空时返回 []。
        2. 用 numpy 计算 query 与每个块向量的余弦相似度。
        3. 取相似度最高的 top_k，组装成上面的结构返回。
        提示: 余弦相似度 = a·b / (|a||b|)；可用 np.dot 与 np.linalg.norm。
        """
        if len(self) == 0:                        # ① 空库先挡掉，否则下面在空数组上算会出错
            return []

        q = np.array(query_embedding)             # 形状 (dim,)
        M = np.array(self.embeddings)             # 形状 (N, dim)：N 个块，每块一行

        # ② 一次算出 q 与每个块的余弦相似度
        dots  = M @ q                             # (N,) 每个块和 q 的点积 a·b
        norms = np.linalg.norm(M, axis=1) * np.linalg.norm(q)   # 每个块的 |a| 乘上 |q|
        scores = dots / (norms + 1e-8)            # +1e-8 防止除以零

        # ③ 取分数最高的 top_k 个块的下标
        order = np.argsort(scores)[::-1][:top_k]  # argsort 升序 → 反转成降序 → 切前 top_k

        return [
            {"text": self.texts[i], "score": float(scores[i]), "metadata": self.metadatas[i]}
            for i in order
        ]


# 共享实例：ingest 入库与 knowledge_base 检索都用它
STORE = VectorStore()
