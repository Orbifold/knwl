import json
from typing import cast

from fastmcp.resources import TextResource

from tests.fixtures import *


@pytest.mark.asyncio
async def test_tools(mcp_client):
    async with mcp_client:
        works = await mcp_client.ping()
        assert works

    async with mcp_client:
        tool_names = [u.name for u in await mcp_client.list_tools()]
        assert "namespace" in tool_names
        # call the tool
        found = await mcp_client.call_tool("namespace")
        assert found is not None
        assert found.data == "default"


@pytest.mark.asyncio
async def test_resources(mcp_client):
    async with mcp_client:
        resources = await mcp_client.list_resources()
        assert resources is not None
        assert "info" in [r.name for r in resources]
        info = await mcp_client.read_resource("text://info")
        d = json.loads(cast(TextResource, info[0]).text)
        print(d)
        assert "version" in d
