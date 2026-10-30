"""Register/test Yuque with the live DB-GPT API, then read a real doc via MCP."""

import asyncio
import json
import os
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv, set_key
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from yuque_mcp import DEFAULT_API_BASE, ROOT

ENDPOINT = "http://127.0.0.1:5671/mcp"
CONNECTORS = "http://127.0.0.1:5670/api/v2/serve/connectors"
REPORT = ROOT / "work" / "yuque-connector-check.json"


def error_message(exc):
    if isinstance(exc, BaseExceptionGroup):
        return "; ".join(error_message(child) for child in exc.exceptions)
    return str(exc)


def api(client, method: str, path: str, **kwargs):
    response = client.request(method, CONNECTORS + path, **kwargs)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise ValueError(payload.get("err_msg") or "DB-GPT 连接器接口失败")
    return payload["data"]


async def call(session, name: str, arguments=None):
    result = await session.call_tool(name, arguments=arguments or {})
    if result.isError:
        # Our bridge returns bounded errors without including token or body.
        raise ValueError("; ".join(item.text for item in result.content if item.type == "text"))
    if result.structuredContent is not None:
        data = result.structuredContent
        return data.get("result", data)
    return json.loads(next(item.text for item in result.content if item.type == "text"))


async def check_document(report):
    async with streamablehttp_client(ENDPOINT) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            url = os.getenv("YUQUE_DOC_URL", "").strip()
            user = None
            try:
                user = await call(session, "yuque_get_user")
                report["account_verified"] = True
                report["account_login"] = user["login"]
            except ValueError as exc:
                report["account_error"] = str(exc)
                if not url:
                    raise
            if not url:
                # Find one readable non-empty document, with bounded pagination.
                for repo_offset in range(0, 500, 100):
                    repos = await call(session, "yuque_list_repos", {"login": user["login"], "offset": repo_offset})
                    if not repos:
                        break
                    for repo in repos:
                        namespace = repo.get("namespace") or str(repo["id"])
                        docs = await call(session, "yuque_list_docs", {"namespace": namespace})
                        if docs:
                            if "/" not in namespace:
                                namespace = f"{user['login']}/{repo['slug']}"
                            host = os.getenv("YUQUE_API_BASE", DEFAULT_API_BASE).split("/api/")[0]
                            url = f"{host}/{namespace}/{docs[0]['slug']}"
                            break
                    if url:
                        break
            if not url:
                raise ValueError("账户验证通过，但未发现文档；请在 .env 填写 YUQUE_DOC_URL")
            report["document_url"] = url
            try:
                doc = await call(session, "yuque_get_doc", {"url": url})
            except ValueError as exc:
                report["document_error"] = str(exc)
                raise
            report.update(document_read=True, document_url=url, document_title=doc["title"], body_characters=len(doc["body"]))
            set_key(ROOT / ".env", "YUQUE_DOC_URL", url)
            if not report["account_verified"]:
                raise ValueError(report["account_error"])


def main():
    load_dotenv(ROOT / ".env", override=True)
    if not os.getenv("YUQUE_TOKEN", "").strip():
        raise SystemExit("请先在 .env 配置 YUQUE_TOKEN，再运行 scripts/start_yuque.ps1")
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "success": False,
              "mcp_endpoint": ENDPOINT, "account_verified": False, "document_read": False}
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            instances = api(client, "GET", "/")
            existing = next((row for row in instances if row["connector_type"] == "yuque" and (row.get("config") or {}).get("server_uri") == ENDPOINT), None)
            payload = {"display_name": "语雀文档", "credentials": {}, "config": {
                "server_uri": ENDPOINT, "transport": "streamable_http", "auth_type": "none",
                "description": "读取语雀账户、知识库、文档列表和正文；Token 由本地 MCP 服务加载"}}
            if existing:
                row = api(client, "PUT", "/" + existing["connector_id"], json=payload)
            else:
                row = api(client, "POST", "/", json={"connector_type": "yuque", **payload})
            cid = report["connector_id"] = row["connector_id"]
            probe = api(client, "POST", f"/{cid}/test")
            report["transport_verified"] = probe["success"]
            if not probe["success"]:
                raise ValueError(probe["message"])
            tools = api(client, "GET", f"/{cid}/tools")
            report["tools"] = [tool["name"] for tool in tools["tools"]]
            expected = {"yuque_get_user", "yuque_list_repos", "yuque_list_docs", "yuque_get_doc"}
            if {tool["original_name"] for tool in tools["tools"]} != expected:
                raise ValueError("连接器工具清单不完整")
        asyncio.run(check_document(report))
        report["success"] = True
    except Exception as exc:
        # Do not persist credentials, request headers, or document content.
        report["error"] = error_message(exc).replace(os.getenv("YUQUE_TOKEN", ""), "[REDACTED]")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["success"] else 1)


if __name__ == "__main__":
    main()
