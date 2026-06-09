"""Tests for the LLM client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.llm.models import LLMConfig, LLMResponse, ModelProvider
from backend.llm.client import LLMClient


@pytest.fixture
def client():
    return LLMClient(
        anthropic_key="test-anthropic-key",
        openai_key="test-openai-key",
        deepseek_key="test-deepseek-key",
    )


@pytest.fixture
def anthropic_config():
    return LLMConfig(model="claude-3-5-sonnet-20241022", temperature=0.7, max_tokens=1000)


@pytest.fixture
def openai_config():
    return LLMConfig(model="gpt-4o", temperature=0.7, max_tokens=1000)


@pytest.fixture
def deepseek_config():
    return LLMConfig(model="deepseek-v4-pro", temperature=0.7, max_tokens=1000)


class TestGetProvider:
    """Test provider detection from model name."""

    def test_claude_is_anthropic(self):
        assert LLMClient._get_provider("claude-3-5-sonnet") == ModelProvider.ANTHROPIC

    def test_gpt_is_openai(self):
        assert LLMClient._get_provider("gpt-4o") == ModelProvider.OPENAI

    def test_deepseek_is_deepseek(self):
        assert LLMClient._get_provider("deepseek-v4-pro") == ModelProvider.DEEPSEEK


class TestCallAnthropicSuccess:
    """Test successful Anthropic API call."""

    @pytest.mark.asyncio
    async def test_call_anthropic_success(self, client, anthropic_config):
        """Mock Anthropic client and verify response format."""
        mock_anthropic = MagicMock()
        mock_messages = MagicMock()
        mock_messages.create = AsyncMock(return_value=MagicMock(
            content=[MagicMock(text="Hello from Claude")],
            model="claude-3-5-sonnet-20241022",
            usage=MagicMock(input_tokens=10, output_tokens=5),
        ))
        mock_anthropic.messages = mock_messages

        with patch("backend.llm.client.AsyncAnthropic", return_value=mock_anthropic):
            client._anthropic_client = mock_anthropic
            response = await client.call("Say hello", anthropic_config)

        assert isinstance(response, LLMResponse)
        assert response.content == "Hello from Claude"
        assert response.model == "claude-3-5-sonnet-20241022"
        assert response.usage is not None
        assert response.usage["input_tokens"] == 10
        assert response.usage["output_tokens"] == 5
        mock_messages.create.assert_awaited_once()


class TestCallFallbackOnFailure:
    """Test fallback to alternative provider on failure."""

    @pytest.mark.asyncio
    async def test_call_fallback_on_failure(self, client, anthropic_config):
        """Mock Anthropic to fail, verify fallback to OpenAI works."""
        # Anthropic fails
        mock_anthropic = MagicMock()
        mock_messages = MagicMock()
        mock_messages.create = AsyncMock(side_effect=Exception("Anthropic API error"))
        mock_anthropic.messages = mock_messages

        # OpenAI succeeds
        mock_openai = MagicMock()
        mock_chat = MagicMock()
        mock_chat.completions = MagicMock()
        mock_chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="Hello from GPT"))],
            model="gpt-4o",
            usage=MagicMock(prompt_tokens=10, completion_tokens=5),
        ))
        mock_openai.chat = mock_chat

        with patch("backend.llm.client.AsyncAnthropic", return_value=mock_anthropic):
            with patch("backend.llm.client.AsyncOpenAI", return_value=mock_openai):
                client._anthropic_client = mock_anthropic
                client._openai_client = mock_openai
                response = await client.call("Say hello", anthropic_config)

        assert isinstance(response, LLMResponse)
        assert response.content == "Hello from GPT"
        assert response.model == "gpt-4o"
        assert response.usage is not None
        mock_messages.create.assert_awaited()
        mock_chat.completions.create.assert_awaited_once()


class TestCallDeepSeekSuccess:
    """Test successful DeepSeek API call."""

    @pytest.mark.asyncio
    async def test_call_deepseek_success(self, client, deepseek_config):
        """Mock DeepSeek client and verify response format."""
        mock_deepseek = MagicMock()
        mock_chat = MagicMock()
        mock_chat.completions = MagicMock()
        mock_chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="Hello from DeepSeek"))],
            model="deepseek-v4-pro",
            usage=MagicMock(prompt_tokens=10, completion_tokens=5),
        ))
        mock_deepseek.chat = mock_chat

        with patch("backend.llm.client.AsyncOpenAI", return_value=mock_deepseek):
            client._deepseek_client = mock_deepseek
            response = await client.call("Say hello", deepseek_config)

        assert isinstance(response, LLMResponse)
        assert response.content == "Hello from DeepSeek"
        assert response.model == "deepseek-v4-pro"
        assert response.usage is not None
        assert response.usage["input_tokens"] == 10
        assert response.usage["output_tokens"] == 5
        mock_chat.completions.create.assert_awaited_once()


class TestDeepSeekFallback:
    """Test DeepSeek fallback to Anthropic on failure."""

    @pytest.mark.asyncio
    async def test_deepseek_fallback(self, client, deepseek_config):
        """Mock DeepSeek to fail, verify fallback to Anthropic works."""
        # DeepSeek fails
        mock_deepseek = MagicMock()
        mock_chat = MagicMock()
        mock_chat.completions = MagicMock()
        mock_chat.completions.create = AsyncMock(side_effect=Exception("DeepSeek API error"))
        mock_deepseek.chat = mock_chat

        # Anthropic succeeds
        mock_anthropic = MagicMock()
        mock_messages = MagicMock()
        mock_messages.create = AsyncMock(return_value=MagicMock(
            content=[MagicMock(text="Hello from Claude")],
            model="claude-3-5-sonnet-20241022",
            usage=MagicMock(input_tokens=10, output_tokens=5),
        ))
        mock_anthropic.messages = mock_messages

        with patch("backend.llm.client.AsyncOpenAI", return_value=mock_deepseek):
            with patch("backend.llm.client.AsyncAnthropic", return_value=mock_anthropic):
                client._deepseek_client = mock_deepseek
                client._anthropic_client = mock_anthropic
                response = await client.call("Say hello", deepseek_config)

        assert isinstance(response, LLMResponse)
        assert response.content == "Hello from Claude"
        assert response.model == "claude-3-5-sonnet-20241022"
        mock_chat.completions.create.assert_awaited()
        mock_messages.create.assert_awaited_once()
