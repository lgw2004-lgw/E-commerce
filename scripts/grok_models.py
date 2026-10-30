"""Register xAI Grok with the project's DB-GPT model registry.

Uses xAI's OpenAI-compatible Chat Completions endpoint. Credentials are supplied
through the model form or XAI_API_KEY, independently of other providers.
"""

from dataclasses import dataclass, field
import os
from typing import Optional

from dbgpt.core import ModelMetadata
from dbgpt.model.proxy.base import register_proxy_model_adapter
from dbgpt.model.proxy.llms.chatgpt import (
    OpenAICompatibleDeployModelParameters,
    OpenAILLMClient,
)

DEFAULT_API_BASE = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.7"


@dataclass
class GrokDeployModelParameters(OpenAICompatibleDeployModelParameters):
    provider: str = "proxy/grok"
    api_base: Optional[str] = field(
        default="${env:XAI_API_BASE:-https://api.x.ai/v1}",
        metadata={"help": "xAI Grok API 地址，默认 https://api.x.ai/v1。"},
    )
    api_key: Optional[str] = field(
        default="${env:XAI_API_KEY}",
        metadata={"help": "xAI API Key，可在此填写或配置 XAI_API_KEY。", "tags": "privacy"},
    )
    context_length: Optional[int] = field(
        default=500000,
        metadata={"help": "Grok 4.7 的上下文长度为 500000；使用其他模型时请按实际限制填写。"},
    )


class GrokLLMClient(OpenAILLMClient):
    """Use the shared streaming/non-streaming client with isolated xAI defaults."""

    def __init__(
        self,
        api_key=None,
        api_base=None,
        model=None,
        model_alias=None,
        context_length=None,
        **kwargs,
    ):
        key = self._resolve_env_vars(api_key) or os.getenv("XAI_API_KEY")
        base = self._resolve_env_vars(api_base) or os.getenv("XAI_API_BASE") or DEFAULT_API_BASE
        if not key:
            raise ValueError("请填写 xAI API Key，或设置 XAI_API_KEY 环境变量。")
        model = model or DEFAULT_MODEL
        super().__init__(
            api_key=key,
            api_base=base,
            model=model,
            model_alias=model_alias or model,
            context_length=context_length or 500000,
            **kwargs,
        )

    @classmethod
    def param_class(cls):
        return GrokDeployModelParameters


register_proxy_model_adapter(
    GrokLLMClient,
    supported_models=[
        ModelMetadata(
            model=DEFAULT_MODEL,
            context_length=500000,
            function_calling=True,
            description=(
                "xAI Grok 4.7：通过兼容聊天接口接入。填写 xAI API Key；"
                "也可手动输入账户支持的其他 Grok 聊天模型名称。"
            ),
            link="https://docs.x.ai/developers/model-capabilities/legacy/chat-completions",
        ),
    ],
)
