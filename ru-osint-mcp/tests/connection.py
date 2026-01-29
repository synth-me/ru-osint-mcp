#!/usr/bin/env python3
"""Simple MCP client to test stdio server connection."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_connection(server_script: str):
    """Test connection to MCP server and list tools."""
    
    # Setup server parameters
    server_params = StdioServerParameters(
        command="python",
        args=[server_script]
    )
    
    # Connect to server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            print("✓ Connected to server")
            
            # List tools
            response = await session.list_tools()
            print(f"\n✓ Found {len(response.tools)} tools:")
            for tool in response.tools:
                print(f"  - {tool.name}")

if __name__ == "__main__":

    asyncio.run(test_connection("../main.py"))