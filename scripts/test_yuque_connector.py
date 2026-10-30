"""Offline protocol and real local MCP routing checks; no Yuque credentials."""

import asyncio
import json
import socket
import unittest

import httpx
import uvicorn

from dbgpt.agent.resource.connector.manager import ConnectorManager, ConnectorStatus
from yuque_mcp import ROOT, YuqueClient, create_server, parse_doc_url


class YuqueProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_api_auth_errors_and_content_are_not_leaked(self):
        def handle(request):
            self.assertEqual(request.headers["X-Auth-Token"], "offline-test-token")
            return httpx.Response(429, text="private upstream details")
        client = YuqueClient("offline-test-token", transport=httpx.MockTransport(handle))
        with self.assertRaisesRegex(ValueError, "HTTP 429") as caught:
            await client.get("/user")
        self.assertNotIn("private", str(caught.exception))
        self.assertNotIn("offline-test-token", str(caught.exception))

    async def test_cross_host_and_path_traversal_rejected(self):
        for url in ("https://evil.example/a/b/c", "https://www.yuque.com/a/b/%2e%2e", "https://www.yuque.com/a/b/c%2Fd"):
            with self.assertRaises(ValueError):
                parse_doc_url(url)
        self.assertEqual(parse_doc_url("https://www.yuque.com/team/book/doc?x=1#heading"), ("team/book", "doc"))

    async def test_real_mcp_manager_discovers_and_executes_prefixed_doc_tool(self):
        seen = []
        def handle(request):
            seen.append(str(request.url))
            self.assertEqual(request.headers["X-Auth-Token"], "offline-test-token")
            self.assertEqual(request.url.path, "/api/v2/repos/team/book/docs/doc")
            self.assertEqual(request.url.params["raw"], "1")
            return httpx.Response(200, json={"data": {"id": 7, "title": "测试文档", "body": "# 指标口径\n净销售额 = 销售额 - 退款", "format": "markdown"}})

        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        bridge = create_server(YuqueClient("offline-test-token", transport=httpx.MockTransport(handle)), port)
        server = uvicorn.Server(uvicorn.Config(bridge.streamable_http_app(), log_level="error", lifespan="on"))
        task = asyncio.create_task(server.serve(sockets=[listener]))
        try:
            async with asyncio.timeout(5):
                while not server.started:
                    await asyncio.sleep(0.02)
            manager = ConnectorManager()
            manager.load_catalog(str(ROOT / "DB-GPT/packages/dbgpt-ext/src/dbgpt_ext/connector/catalog.json"))
            cid = await manager.create_connector("yuque", {}, name="语雀测试", extra_config={"server_uri": f"http://127.0.0.1:{port}/mcp", "transport": "streamable_http"})
            self.assertEqual(manager.get_status(cid), ConnectorStatus.active)
            tools = manager.get_connector_tools(cid).sub_resources
            self.assertEqual(len(tools), 4)
            tool = next(t for t in tools if t.name == "mcp__yuque__yuque_get_doc")
            result = await tool.async_execute(url="https://www.yuque.com/team/book/doc")
            self.assertFalse(result.isError)
            doc = json.loads(result.content[0].text)
            self.assertEqual(doc["title"], "测试文档")
            self.assertIn("净销售额", doc["body"])
            self.assertEqual(len(seen), 1)
        finally:
            server.should_exit = True
            await asyncio.wait_for(task, timeout=5)
            listener.close()


if __name__ == "__main__":
    unittest.main()
