import asyncio

from mcp import Client

from app.mcp.server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()

        print("Available tools:")
        for tool in tools.tools:
            print(f"- {tool.name}")

        search_result = await client.call_tool(
            "search_products",
            {
                "query": "laptop",
            },
        )

        print("Search result:")
        print(search_result)

        order_result = await client.call_tool(
            "get_order_status",
            {
                "order_id": 46,
            },
        )

        print("Order result:")
        print(order_result)


if __name__ == "__main__":
    asyncio.run(main())