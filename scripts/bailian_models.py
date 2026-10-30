"""Alibaba Cloud Model Studio adapters registered by the local server launcher.

Embedding uses the OpenAI-compatible endpoint. Reranking uses DashScope's
native nested request/response format, preserving the original document order
expected by DB-GPT. No credentials are embedded in this module.
"""

from dataclasses import dataclass
import math

import aiohttp

from dbgpt.core import EmbeddingModelMetadata
from dbgpt.model.adapter.base import register_embedding_adapter
from dbgpt.rag.embedding.embeddings import (
    OpenAPIEmbeddingDeployModelParameters,
    OpenAPIEmbeddings,
)
from dbgpt.rag.embedding.rerank import (
    OpenAPIRerankerDeployModelParameters,
    OpenAPIRerankEmbeddings,
)


@dataclass
class BailianEmbeddingParameters(OpenAPIEmbeddingDeployModelParameters):
    provider: str = "proxy/bailian"


class BailianEmbeddings(OpenAPIEmbeddings):
    """Respect the text-embedding-v4 limit of ten inputs per request."""

    @classmethod
    def param_class(cls):
        return BailianEmbeddingParameters

    def embed_documents(self, texts):
        vectors = []
        for start in range(0, len(texts), 10):
            vectors.extend(super().embed_documents(texts[start:start + 10]))
        return vectors

    async def aembed_documents(self, texts):
        vectors = []
        for start in range(0, len(texts), 10):
            vectors.extend(await super().aembed_documents(texts[start:start + 10]))
        return vectors


@dataclass
class BailianRerankerParameters(OpenAPIRerankerDeployModelParameters):
    provider: str = "proxy/bailian"


class BailianRerankEmbeddings(OpenAPIRerankEmbeddings):
    """Convert native DashScope ranking results to input-aligned scores."""

    @classmethod
    def param_class(cls):
        return BailianRerankerParameters

    def _request_body(self, query, candidates):
        return {
            "model": self.model_name,
            "input": {"query": query, "documents": candidates},
            "parameters": {"top_n": len(candidates), "return_documents": False},
        }

    @staticmethod
    def _scores(response, count):
        results = response.get("output", {}).get("results")
        if not isinstance(results, list) or len(results) != count:
            raise RuntimeError("Bailian reranker did not return all document scores")
        scores = [None] * count
        for result in results:
            index = result.get("index")
            if type(index) is not int or not 0 <= index < count or scores[index] is not None:
                raise RuntimeError("Bailian reranker returned an invalid document index")
            score = float(result["relevance_score"])
            if not math.isfinite(score):
                raise RuntimeError("Bailian reranker returned a non-finite score")
            scores[index] = score
        return scores

    def predict(self, query, candidates):
        if not candidates:
            return []
        response = self.session.post(
            self.api_url,
            json=self._request_body(query, candidates),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return self._scores(response.json(), len(candidates))

    async def apredict(self, query, candidates):
        if not candidates:
            return []
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as session:
            async with session.post(
                self.api_url, json=self._request_body(query, candidates)
            ) as response:
                response.raise_for_status()
                return self._scores(await response.json(), len(candidates))


register_embedding_adapter(
    BailianEmbeddings,
    supported_models=[EmbeddingModelMetadata(model="text-embedding-v4", dimension=1024)],
)
register_embedding_adapter(
    BailianRerankEmbeddings,
    supported_models=[EmbeddingModelMetadata(model="qwen3-rerank")],
)
