"""Tests for query_structured_via_agent."""

from unittest.mock import patch

import pytest
from pydantic import BaseModel

from skillet._internal.sdk.query_result import QueryResult
from skillet.agent import Agent

from .query_structured_via_agent import query_structured_via_agent


class Sample(BaseModel):
    name: str
    value: int


class _StubRunAgent:
    """Queue agent replies and capture how run_agent was called."""

    def __init__(self, *replies: str):
        self._replies = list(replies)
        self.calls: list[dict] = []

    async def __call__(self, agent, prompts, *, allowed_tools=None, cwd=None, env=None):
        self.calls.append(
            {
                "agent": agent,
                "prompts": prompts,
                "allowed_tools": allowed_tools,
                "cwd": cwd,
                "env": env,
            }
        )
        return QueryResult(text=self._replies.pop(0))


def _patch_run_agent(stub: _StubRunAgent):
    return patch(
        "skillet._internal.agent.query_structured_via_agent.run_agent",
        stub,
    )


def describe_query_structured_via_agent():
    @pytest.mark.asyncio
    async def it_parses_a_raw_json_object_reply():
        stub = _StubRunAgent('{"name": "test", "value": 42}')
        with _patch_run_agent(stub):
            result = await query_structured_via_agent("summarize", Sample, Agent.CODEX)

        assert isinstance(result, Sample)
        assert result.name == "test"
        assert result.value == 42

    @pytest.mark.asyncio
    async def it_extracts_json_from_a_markdown_fence():
        stub = _StubRunAgent('```json\n{"name": "fenced", "value": 1}\n```')
        with _patch_run_agent(stub):
            result = await query_structured_via_agent("p", Sample, Agent.CLAUDE)

        assert result.name == "fenced"

    @pytest.mark.asyncio
    async def it_extracts_json_embedded_in_prose():
        stub = _StubRunAgent('Here you go: {"name": "prose", "value": 7} -- done.')
        with _patch_run_agent(stub):
            result = await query_structured_via_agent("p", Sample, Agent.CLAUDE)

        assert result.name == "prose"
        assert result.value == 7

    @pytest.mark.asyncio
    async def it_unwraps_a_single_key_wrapper():
        stub = _StubRunAgent('{"output": {"name": "wrapped", "value": 3}}')
        with _patch_run_agent(stub):
            result = await query_structured_via_agent("p", Sample, Agent.CODEX)

        assert result.name == "wrapped"
        assert result.value == 3

    @pytest.mark.asyncio
    async def it_injects_the_model_schema_into_the_prompt():
        stub = _StubRunAgent('{"name": "x", "value": 1}')
        with _patch_run_agent(stub):
            await query_structured_via_agent("Original prompt body", Sample, Agent.CODEX)

        sent = stub.calls[0]["prompts"][0]
        assert "Original prompt body" in sent
        # The JSON schema field names must reach the agent.
        assert '"name"' in sent
        assert '"value"' in sent

    @pytest.mark.asyncio
    async def it_routes_through_the_selected_agent_with_no_tools():
        stub = _StubRunAgent('{"name": "x", "value": 1}')
        with _patch_run_agent(stub):
            await query_structured_via_agent("p", Sample, Agent.CODEX)

        assert stub.calls[0]["agent"] is Agent.CODEX
        assert stub.calls[0]["allowed_tools"] == []

    @pytest.mark.asyncio
    async def it_retries_once_on_an_unparseable_reply_then_succeeds():
        stub = _StubRunAgent("not json at all", '{"name": "ok", "value": 9}')
        with _patch_run_agent(stub):
            result = await query_structured_via_agent("p", Sample, Agent.CLAUDE)

        assert result.value == 9
        assert len(stub.calls) == 2
        # The retry prompt is stricter than the first attempt.
        assert stub.calls[1]["prompts"][0] != stub.calls[0]["prompts"][0]

    @pytest.mark.asyncio
    async def it_raises_after_exhausting_retries():
        stub = _StubRunAgent("garbage", "still garbage")
        with _patch_run_agent(stub), pytest.raises(ValueError, match="Sample"):
            await query_structured_via_agent("p", Sample, Agent.CODEX)

        assert len(stub.calls) == 2

    @pytest.mark.asyncio
    async def it_raises_when_reply_json_is_not_an_object():
        stub = _StubRunAgent("[1, 2, 3]", "[4, 5]")
        with _patch_run_agent(stub), pytest.raises(ValueError):
            await query_structured_via_agent("p", Sample, Agent.CODEX)
