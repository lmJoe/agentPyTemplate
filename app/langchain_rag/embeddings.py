import hashlib
import math
import re
from collections import Counter

from langchain_core.embeddings import Embeddings

#   简单的哈希 Embedding 实现，仅用于教学演示。

class SimpleHashEmbeddings(Embeddings):
    """
    教学用本地 Embedding。

    说明：
    1. 不需要 API Key。
    2. 可以跑通 RAG 流程。
    3. 不适合生产环境。
    4. 生产环境请替换为 OpenAIEmbeddings / Qwen Embeddings / bge 等。
    """

    def __init__(self, dimension: int = 128):
        self.dimension = dimension


    #   对文档列表进行嵌入，返回嵌入后的向量列表
    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        # 对每个文档进行嵌入
        # 并返回嵌入后的向量列表
        return [
            self._embed(text)
            for text in texts
        ]


    #   对查询进行嵌入，返回嵌入后的向量
    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        return self._embed(text)


    #   对文档列表进行嵌入，返回嵌入后的向量列表
    def _embed(self, text: str) -> list[float]:

        # 对文本进行分词
        tokens = self._tokenize(text)

        # 并统计每个词的出现次数
        counter = Counter(tokens)

        # 计算每个词的哈希值，并将其转换为索引，并累加到向量中
        vector = [0.0] * self.dimension
        for token, count in counter.items():
            index = self._hash_to_index(token)
            vector[index] += float(count)

        # 归一化向量
        return self._normalize(vector)


    #   对文本进行分词，返回分词后的词列表
    def _tokenize(self, text: str) -> list[str]:
        # 对文本进行分词，返回分词后的词列表
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
        # 对英文单词进行分词
        english_words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        # 返回中文和英文单词的列表
        return chinese_chars + english_words

    #   对词进行哈希，返回哈希后的索引
    def _hash_to_index(self, token: str) -> int:
        # 对词进行哈希，返回哈希后的索引
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        # 将哈希值转换为整数，并取模 self.dimension，得到索引
        return int(digest, 16) % self.dimension


    #   归一化向量，返回归一化后的向量
    def _normalize(
        self,
        vector: list[float],
    ) -> list[float]:
        # 计算向量的范数
        norm = math.sqrt(sum(value * value for value in vector))
        # 如果范数为 0，则返回原向量
        if norm == 0:
            return vector
        # 否则，返回归一化后的向量
        return [
            value / norm
            for value in vector
        ]


#   创建 Embeddings 对象，返回 Embeddings 对象
def create_embeddings() -> Embeddings:
    return SimpleHashEmbeddings(
        dimension=128,
    )