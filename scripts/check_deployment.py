"""Exercise real DB-GPT HTTP routes against the synthetic commerce datasource.

This checks deployment/SQL execution, not an LLM's Text-to-SQL accuracy.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:5670"
session = requests.Session()
session.trust_env = False
checks = []


def request(method, path, **kwargs):
    response = session.request(method, BASE + path, timeout=30, **kwargs)
    response.raise_for_status()
    return response


def result(method, path, **kwargs):
    payload = request(method, path, **kwargs).json()
    assert payload.get("success") is True, payload
    return payload["data"]


page = request("GET", "/")
assert "_next/static/" in page.text
checks.append({"check": "web_ui", "passed": True})
datasources = result("GET", "/api/v1/chat/db/list")
assert any(source["db_name"] == "ecommerce_demo" for source in datasources)
checks.append({"check": "datasource_registered", "passed": True})
connected = result("POST", "/api/v2/serve/datasources/test-connection", json={"type": "sqlite", "params": {"path": (ROOT / "data/ecommerce.db").as_posix()}})
assert connected is True, connected
checks.append({"check": "datasource_connection", "passed": True})
tables = result("GET", "/api/v1/editor/db/tables", params={"db_name": "ecommerce_demo", "page_index": 1, "page_size": 100})
names = {node["title"] for node in tables["children"]}
assert {"customers", "products", "orders", "order_items", "refunds"} <= names, names
checks.append({"check": "schema_introspection", "passed": True})

cases = json.loads((ROOT / "data/benchmark.json").read_text(encoding="utf-8"))
for case in cases:
    started = time.perf_counter()
    data = result("POST", "/api/v1/editor/sql/run", json={"db_name": "ecommerce_demo", "sql": case["reference_sql"]})
    assert not data.get("result_info"), data
    expected = [[str(value) if value is not None else None for value in row.values()] for row in case["expected_rows"]]
    assert data["values"] == expected, {"id": case["id"], "actual": data["values"][:3], "expected": expected[:3]}
    checks.append({"check": f"reference_sql_{case['id']:02d}", "passed": True, "rows": len(expected), "http_ms": round((time.perf_counter() - started) * 1000, 2)})

report = {"checked_at": datetime.now(timezone.utc).isoformat(), "base_url": BASE,
          "scope": "UI, datasource registration/connection/schema, reference SQL execution. No LLM accuracy measurement.",
          "passed": len(checks), "checks": checks}
(ROOT / "work/deployment-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
