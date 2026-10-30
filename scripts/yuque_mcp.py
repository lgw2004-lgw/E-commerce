"""Local, read-only Yuque Open API bridge for DB-GPT's existing MCP connector."""

import os
import re
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API_BASE = "https://www.yuque.com/api/v2"
PORT = 5671


def segment(value: str) -> str:
    value = unquote(value).strip()
    if not re.fullmatch(r"[\w-]+", value):
        raise ValueError("语雀路径只接受用户名、知识库标识或文档标识")
    return quote(value, safe="")


def namespace_path(namespace: str) -> str:
    parts = namespace.strip("/").split("/")
    if len(parts) not in (1, 2):
        raise ValueError("namespace 应为知识库 ID 或 用户名/知识库标识")
    return "/".join(segment(part) for part in parts)


def parse_doc_url(url: str, api_base: str = DEFAULT_API_BASE) -> tuple[str, str]:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != urlsplit(api_base).netloc:
        raise ValueError("文档地址必须与 YUQUE_API_BASE 属于同一 HTTPS 站点")
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 3:
        raise ValueError("文档地址应为 https://www.yuque.com/用户名/知识库/文档")
    namespace = namespace_path("/".join(parts[:2]))
    return namespace, segment(parts[2])


class YuqueClient:
    def __init__(self, token: str, api_base: str = DEFAULT_API_BASE, transport=None):
        if not token.strip():
            raise ValueError("请先在项目 .env 配置 YUQUE_TOKEN")
        parsed = urlsplit(api_base)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
            raise ValueError("YUQUE_API_BASE 必须是 HTTPS API 地址")
        self.token = token.strip()
        self.api_base = api_base.rstrip("/")
        self.transport = transport

    async def get(self, path: str, **params):
        try:
            async with httpx.AsyncClient(
                transport=self.transport, timeout=20, follow_redirects=False,
                headers={"X-Auth-Token": self.token, "User-Agent": "ecommerce-ai-analytics/yuque", "Accept": "application/json"},
            ) as client:
                response = await client.get(self.api_base + path, params=params)
        except httpx.RequestError:
            raise ValueError("语雀 API 网络连接失败或超时") from None
        if not response.is_success:
            hints = {401: "Token 无效或已过期", 403: "Token 无读取权限或账号无 API 权限", 404: "文档/知识库不存在或无权访问", 429: "请求过于频繁，请稍后重试"}
            raise ValueError(f"语雀 API HTTP {response.status_code}: {hints.get(response.status_code, '请求失败')}")
        try:
            payload = response.json()
            if not isinstance(payload, dict) or "data" not in payload:
                raise ValueError()
            return payload["data"]
        except (ValueError, TypeError):
            raise ValueError("语雀 API 返回格式异常，未收到 data 数据") from None


def create_server(client: YuqueClient, port: int = PORT) -> FastMCP:
    server = FastMCP("Yuque", host="127.0.0.1", port=port, stateless_http=True, json_response=True)

    @server.tool()
    async def yuque_get_user() -> dict:
        """验证语雀 Token，读取当前用户。连接验收时先调用此工具。"""
        data = await client.get("/user")
        return {key: data.get(key) for key in ("id", "login", "name")}

    @server.tool()
    async def yuque_list_repos(login: str, offset: int = 0) -> list:
        """列出用户或团队的知识库。login 为用户名/团队标识，offset 用于翻页。"""
        if offset < 0:
            raise ValueError("offset 不能小于 0")
        data = await client.get(f"/users/{segment(login)}/repos", offset=offset)
        return [{key: row.get(key) for key in ("id", "name", "namespace", "slug", "description")} for row in data]

    @server.tool()
    async def yuque_list_docs(namespace: str, offset: int = 0) -> list:
        """列出知识库文档。namespace 为 用户名/知识库标识 或知识库 ID；offset 用于翻页。"""
        if offset < 0:
            raise ValueError("offset 不能小于 0")
        data = await client.get(f"/repos/{namespace_path(namespace)}/docs", offset=offset)
        return [{key: row.get(key) for key in ("id", "slug", "title", "description", "updated_at")} for row in data]

    @server.tool()
    async def yuque_get_doc(url: str) -> dict:
        """按完整语雀文档 URL 读取正文。返回 title、body、format，可用于总结和分析。"""
        namespace, slug = parse_doc_url(url, client.api_base)
        data = await client.get(f"/repos/{namespace}/docs/{slug}", raw=1)
        body = data.get("body") or data.get("body_html") or ""
        if not body.strip():
            raise ValueError("语雀文档正文为空，无法完成正文读取验收")
        return {"id": data.get("id"), "title": data.get("title"), "body": body,
                "format": data.get("format"), "updated_at": data.get("updated_at"), "url": url}

    return server


if __name__ == "__main__":
    load_dotenv(ROOT / ".env", override=True)
    client = YuqueClient(os.getenv("YUQUE_TOKEN", ""), os.getenv("YUQUE_API_BASE", DEFAULT_API_BASE))
    create_server(client).run(transport="streamable-http")
