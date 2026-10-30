"""Offline regression checks for the Model Studio protocol adaptation."""

import asyncio
import unittest
from unittest.mock import patch

from bailian_models import BailianEmbeddings, BailianRerankEmbeddings
from dbgpt.model.adapter.base import get_embedding_adapter
from dbgpt.rag.embedding.embeddings import OpenAPIEmbeddings


class BailianAdapterTests(unittest.TestCase):
    def test_rank_scores_follow_input_order(self):
        payload = {"output": {"results": [
            {"index": 2, "relevance_score": 0.9},
            {"index": 0, "relevance_score": 0.6},
            {"index": 1, "relevance_score": 0.1},
        ]}}
        self.assertEqual(BailianRerankEmbeddings._scores(payload, 3), [0.6, 0.1, 0.9])

    def test_incomplete_or_duplicate_scores_fail(self):
        for results in (
            [{"index": 0, "relevance_score": 0.5}],
            [{"index": 0, "relevance_score": 0.5}] * 2,
            [{"index": -1, "relevance_score": 0.5}] * 2,
        ):
            with self.subTest(results=results), self.assertRaises(RuntimeError):
                BailianRerankEmbeddings._scores({"output": {"results": results}}, 2)

    def test_empty_candidates_do_not_call_api(self):
        model = BailianRerankEmbeddings()
        with patch.object(type(model.session), "post") as post:
            self.assertEqual(model.predict("query", []), [])
            self.assertEqual(asyncio.run(model.apredict("query", [])), [])
            post.assert_not_called()

    def test_native_request_and_response(self):
        model = BailianRerankEmbeddings(model_name="qwen3-rerank")
        with patch.object(type(model.session), "post") as post:
            post.return_value.json.return_value = {"output": {"results": [
                {"index": 1, "relevance_score": 0.8},
                {"index": 0, "relevance_score": 0.2},
            ]}}
            self.assertEqual(model.predict("query", ["a", "b"]), [0.2, 0.8])
            self.assertEqual(post.call_args.kwargs["json"], {
                "model": "qwen3-rerank",
                "input": {"query": "query", "documents": ["a", "b"]},
                "parameters": {"top_n": 2, "return_documents": False},
            })

    def test_embedding_batch_limit_sync_and_async(self):
        model = BailianEmbeddings()
        texts = [str(i) for i in range(23)]
        def embed(_, batch):
            self.assertLessEqual(len(batch), 10)
            return [[int(text)] for text in batch]
        async def aembed(instance, batch):
            return embed(instance, batch)
        with patch.object(OpenAPIEmbeddings, "embed_documents", embed):
            self.assertEqual(model.embed_documents(texts), [[i] for i in range(23)])
            self.assertEqual(model.embed_documents([]), [])
        with patch.object(OpenAPIEmbeddings, "aembed_documents", aembed):
            self.assertEqual(asyncio.run(model.aembed_documents(texts)), [[i] for i in range(23)])

    def test_provider_registration(self):
        for is_rerank, name, expected in (
            (False, "text-embedding-v4", BailianEmbeddings),
            (True, "qwen3-rerank", BailianRerankEmbeddings),
        ):
            adapter = get_embedding_adapter("proxy/bailian", is_rerank, name)
            self.assertIsNotNone(adapter)
            params = adapter.model_param_class()(name=name)
            self.assertIsInstance(adapter.load_from_params(params), expected)


if __name__ == "__main__":
    unittest.main()
