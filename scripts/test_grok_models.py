"""Offline xAI protocol checks: no real key, network request or paid inference."""

from dataclasses import fields
import json
import os
import unittest
from unittest.mock import patch

import httpx
from openai import AsyncOpenAI

from dbgpt.core import ModelRequest
from dbgpt.model.adapter.base import get_model_adapter, get_supported_models
from grok_models import DEFAULT_API_BASE, DEFAULT_MODEL, GrokDeployModelParameters, GrokLLMClient


class GrokConfigurationTests(unittest.TestCase):
    def test_provider_registration_in_creation_catalog(self):
        rows = [m for m in get_supported_models("llm") if m.provider == "proxy/grok"]
        self.assertTrue(any(row.model == DEFAULT_MODEL for row in rows))
        adapter = get_model_adapter("proxy/grok", model_name="grok-custom-alias")
        self.assertIs(adapter.model_param_class(), GrokDeployModelParameters)
        self.assertIs(adapter.get_llm_client_class(None), GrokLLMClient)

    def test_key_is_private_and_not_shared_with_other_providers(self):
        key_field = next(f for f in fields(GrokDeployModelParameters) if f.name == "api_key")
        self.assertEqual(key_field.metadata["tags"], "privacy")
        with patch.dict(os.environ, {"OPENAI_API_KEY": "other-provider-key"}, clear=True):
            with self.assertRaisesRegex(ValueError, "xAI API Key"):
                GrokLLMClient()

    def test_saved_model_parameters_preserve_backend_and_endpoint(self):
        params = GrokDeployModelParameters(
            name="company-grok", backend="grok-account-model", api_key="test-key",
            api_base="https://gateway.example/v1", context_length=131072,
        )
        client = GrokLLMClient.new_client(params)
        self.assertEqual(client.default_model, "grok-account-model")
        self.assertEqual(str(client.client.base_url), "https://gateway.example/v1/")
        self.assertEqual(client._context_length, 131072)


class GrokProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = []
        async def handle(request):
            self.requests.append(request)
            payload = json.loads(request.content)
            self.assertEqual(str(request.url), DEFAULT_API_BASE + "/chat/completions")
            self.assertEqual(request.headers["Authorization"], "Bearer test-xai-key")
            self.assertEqual(payload["model"], DEFAULT_MODEL)
            if payload.get("stream"):
                events = [
                    {"id": "test", "object": "chat.completion.chunk", "created": 0, "model": DEFAULT_MODEL,
                     "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}]}
                    for text in ["模型", "接入成功"]
                ]
                body = "".join("data: " + json.dumps(e, ensure_ascii=False) + "\n\n" for e in events)
                return httpx.Response(200, text=body + "data: [DONE]\n\n", headers={"content-type": "text/event-stream"})
            return httpx.Response(200, json={
                "id": "test", "object": "chat.completion", "created": 0, "model": DEFAULT_MODEL,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "接入成功"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 2, "total_tokens": 4},
            })
        self.sdk = AsyncOpenAI(
            api_key="test-xai-key", base_url=DEFAULT_API_BASE,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
        )
        self.client = GrokLLMClient(api_key="test-xai-key", openai_client=self.sdk)

    async def asyncTearDown(self):
        await self.sdk.close()

    def request(self):
        return ModelRequest(model=DEFAULT_MODEL, messages=[{"role": "user", "content": "测试"}], max_new_tokens=32)

    async def test_non_streaming_completion(self):
        output = await self.client.generate(self.request())
        self.assertEqual(output.error_code, 0)
        self.assertEqual(output.text, "接入成功")
        self.assertEqual(output.usage["total_tokens"], 4)

    async def test_streaming_completion(self):
        outputs = [output async for output in self.client.generate_stream(self.request())]
        self.assertEqual([o.text for o in outputs], ["模型", "模型接入成功"])


if __name__ == "__main__":
    unittest.main()
