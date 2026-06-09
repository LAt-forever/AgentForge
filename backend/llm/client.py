"""LLM client with retry and fallback support."""

import asyncio
import logging

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from backend.llm.models import LLMConfig, LLMResponse, ModelProvider

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for calling LLM APIs with retry and fallback."""

    # Fallback model mapping
    _FALLBACK_MODELS = {
        "claude-3-5-sonnet-20241022": "gpt-4o",
        "claude-3-5-haiku-20241022": "gpt-4o-mini",
        "gpt-4o": "claude-3-5-sonnet-20241022",
        "gpt-4o-mini": "claude-3-5-haiku-20241022",
    }

    def __init__(self, anthropic_key: str, openai_key: str):
        self._anthropic_key = anthropic_key
        self._openai_key = openai_key
        self._anthropic_client: AsyncAnthropic | None = None
        self._openai_client: AsyncOpenAI | None = None

    @property
    def anthropic_client(self) -> AsyncAnthropic:
        if self._anthropic_client is None:
            self._anthropic_client = AsyncAnthropic(api_key=self._anthropic_key)
        return self._anthropic_client

    @property
    def openai_client(self) -> AsyncOpenAI:
        if self._openai_client is None:
            self._openai_client = AsyncOpenAI(api_key=self._openai_key)
        return self._openai_client

    @staticmethod
    def _get_provider(model: str) -> ModelProvider:
        """Return ANTHROPIC if model starts with 'claude', else OPENAI."""
        if model.lower().startswith("claude"):
            return ModelProvider.ANTHROPIC
        return ModelProvider.OPENAI

    async def call(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Call LLM with retry and fallback to alternative provider."""
        last_error: Exception | None = None
        models_to_try = [config.model]

        # Add fallback model if known
        fallback = self._FALLBACK_MODELS.get(config.model)
        if fallback:
            models_to_try.append(fallback)

        for model in models_to_try:
            provider = self._get_provider(model)
            for attempt in range(3):
                try:
                    if provider == ModelProvider.ANTHROPIC:
                        return await self._call_anthropic(prompt, config, model)
                    else:
                        return await self._call_openai(prompt, config, model)
                except Exception as exc:
                    last_error = exc
                    wait_seconds = 2 ** attempt
                    logger.warning(
                        "LLM call failed (model=%s, attempt=%d/%d): %s. Retrying in %ds...",
                        model, attempt + 1, 3, exc, wait_seconds,
                    )
                    if attempt < 2:
                        await asyncio.sleep(wait_seconds)

        raise last_error or RuntimeError("All LLM calls failed")

    async def _call_anthropic(self, prompt: str, config: LLMConfig, model: str) -> LLMResponse:
        """Call Anthropic messages API."""
        kwargs: dict = {
            "model": model,
            "max_tokens": config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        if config.system_prompt:
            kwargs["system"] = config.system_prompt

        response = await self.anthropic_client.messages.create(**kwargs)

        content = ""
        if response.content:
            content = response.content[0].text

        usage = None
        if response.usage:
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

        return LLMResponse(
            content=content,
            model=response.model or model,
            usage=usage,
        )

    async def _call_openai(self, prompt: str, config: LLMConfig, model: str) -> LLMResponse:
        """Call OpenAI chat completions API."""
        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.openai_client.chat.completions.create(
            model=model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            messages=messages,
        )

        content = ""
        if response.choices:
            content = response.choices[0].message.content or ""

        usage = None
        if response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

        return LLMResponse(
            content=content,
            model=response.model or model,
            usage=usage,
        )
