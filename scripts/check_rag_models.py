"""Verify configured Bailian adapters with synthetic text, without logging keys."""

import asyncio
from datetime import datetime, timezone
import json
import math
from pathlib import Path

from dotenv import dotenv_values

from bailian_models import BailianEmbeddings, BailianRerankEmbeddings

ROOT = Path(__file__).resolve().parents[1]


async def check():
    env = dotenv_values(ROOT / ".env")
    key = env["DASHSCOPE_API_KEY"]
    embedding = BailianEmbeddings(
        model_name=env["EMBEDDING_MODEL_NAME"],
        api_url=env["EMBEDDING_API_URL"],
        api_key=key,
    )
    reranker = BailianRerankEmbeddings(
        model_name=env["RERANKER_MODEL_NAME"],
        api_url=env["RERANKER_API_URL"],
        api_key=key,
    )
    documents = ["订单表记录订单金额和支付状态。", "商品表记录商品名称和类目。", "今天天气晴朗。"]
    vectors = embedding.embed_documents(documents)
    assert len(vectors) == len(documents)
    dimension = len(vectors[0])
    assert dimension == 1024
    assert all(len(v) == dimension and all(math.isfinite(x) for x in v) for v in vectors)
    query_vector = await embedding.aembed_query("查询订单销售额")
    assert len(query_vector) == dimension
    scores = reranker.predict("订单金额在哪张表？", documents)
    async_scores = await reranker.apredict("订单金额在哪张表？", documents)
    assert len(scores) == len(async_scores) == len(documents)
    assert max(range(len(scores)), key=scores.__getitem__) == 0
    assert max(range(len(async_scores)), key=async_scores.__getitem__) == 0
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": embedding.model_name,
        "dimensions": dimension,
        "embedding_sync_and_async": "passed",
        "reranker_model": reranker.model_name,
        "reranker_sync_and_async": "passed",
        "scores_in_original_order": scores,
        "scope": "Synthetic text through the same adapters used by the application; no business data.",
    }


if __name__ == "__main__":
    try:
        report = asyncio.run(check())
    except Exception as exc:
        # Do not print exception bodies/headers that might contain credentials.
        print(json.dumps({"passed": False, "error_type": type(exc).__name__}))
        raise SystemExit(1)
    path = ROOT / "work/rag-model-check.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
