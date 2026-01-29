import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- CONFIGURATION ---
# Ensure this points to your server script
SERVER_SCRIPT = "main.py" 
# Ensure the token matches what is in your tokens.sqlite

TEST_TOKEN = "C3jHJ8CEy4-yJ4mrOdW4ig6gSG6EG1AoLYYgI62wPII" 

async def run_test():
    # Configure the server to run in stdio mode
    # We pass the TOKEN via env variables so the middleware can find it
    server_params = StdioServerParameters(
        command="python",
        args=[SERVER_SCRIPT, "stdio"],
        env={"TOKEN": TEST_TOKEN}
    )

    print(f"--- Launching MCP Server: {SERVER_SCRIPT} ---")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Initialize the connection
            await session.initialize()
            print("Client initialized.")

            # 2. List tools (optional, helps verify server is up)
            tools = await session.list_tools()
            print(f"Server provides {len(tools.tools)} tools.")

            # 3. Call the specific tool
            print("\n--- Calling query_ground_forces ---")
            try:
                result = await session.call_tool(
                    "query_ground_forces",
                    arguments={
                        "table": "barracks artillery forces",
                        "oblast": "Moscow",
                        "limit": 50
                    }
                )
                
                print("\n--- RESULTS ---")
                print(result.content[0].text if result.content else "No content returned.")
                
            except Exception as e:
                print(f"\n--- ERROR ---")
                print(f"Tool call failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        pass