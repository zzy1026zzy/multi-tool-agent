"""【学生任务】文档切块 + 嵌入入库。

把 data/docs 下的文本文件读入，切成小块，调用 embedding API 得到向量，
写入 rag.vector_store.STORE。
"""
from rag.vector_store import STORE
from llm import LLMClient
import os

_llm = LLMClient()


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """把长文本切成带重叠的小块。

    TODO: 按 chunk_size 字符切分，相邻块重叠 overlap 字符，返回非空块列表。
    """
    step = chunk_size - overlap               # 每次前进的步长，必须 > 0（否则死循环）
    chunks = []
    start = 0
    while start < len(text):
        piece = text[start : start + chunk_size]
        if piece.strip():                     # 跳过纯空白的块
            chunks.append(piece)
        start += step                         # 前进 step，相邻两块自然重叠了 overlap 个字
    return chunks


def ingest_file(path: str) -> int:
    """读取单个文本文件，切块、嵌入、入库，返回入库的块数。

    TODO:
    1. 读取文件文本。
    2. chunk_text() 切块。
    3. _llm.embed(chunks) 得到向量。
    4. STORE.add(chunks, embeddings, metadatas=[{"doc": path} ...])。
    5. 返回块数。
    """
    text   = open(path, "r", encoding="utf-8").read()  # 读取 path 的全部文本
    chunks = chunk_text(text)
    if not chunks:
        return 0
    embs   = _llm.embed(chunks)               # 一次把整批块嵌入成向量
    metas  = [{"doc": path} for _ in chunks]  # 记下每块来自哪个文件，检索时好显示来源
    STORE.add(chunks, embs, metas)
    return len(chunks)


def ingest_dir(dir_path: str = "data/docs") -> int:
    """把目录下所有 .md/.txt 文件入库，返回总块数。

    TODO: 遍历目录中的 .md/.txt 文件，对每个调用 ingest_file 并累加块数。
    """
    total = 0
    for name in os.listdir(dir_path):
        if name.endswith(".md") or name.endswith(".txt"):
            path = os.path.join(dir_path, name)
            total += ingest_file(path)
    return total
