# agent.py
import asyncio, json, os
from mcp import Client
from mcp.client.stdio import stdio_client
import openai

LLM = openai.AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)

async def run_agent(user_query: str):
    # ① 建立与 MCP Server 的会话
    server_params = {
        "command": "python",
        "args": ["file_server.py"]
    }
    async with stdio_client(server_params) as (read, write):
        async with Client(read, write) as client:
            await client.initialize()          # MCP 握手

            # ② 让 LLM 知道有哪些工具
            tools = await client.list_tools()
            tool_schemas = [t.inputSchema for t in tools]

            # ③ 把工具描述塞进 LLM 请求
            messages = [
                {"role": "system", "content": "You can use the provided tools."},
                {"role": "user", "content": user_query}
            ]
            llm_resp = await LLM.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=[{"type": "function", "function": s} for s in tool_schemas],
                tool_choice="auto"
            )

            # ④ 如果 LLM 决定调用工具
            if llm_resp.choices[0].message.tool_calls:
                call = llm_resp.choices[0].message.tool_calls[0]
                tool_name = call.function.name
                tool_args = json.loads(call.function.arguments)

                # ⑤ 通过 MCP Client 执行
                result = await client.call_tool(tool_name, tool_args)
                print("工具返回：", result)

                # ⑥ 把结果再喂给 LLM，生成自然语言答案
                messages.append(llm_resp.choices[0].message)
                messages.append({"role": "tool",
                                 "tool_call_id": call.id,
                                 "content": result.content})
                final = await LLM.chat.completions.create(
                    model="gpt-4o-mini", messages=messages
                )
                print("最终回答：", final.choices[0].message.content)

if __name__ == "__main__":
    asyncio.run(run_agent("请把当前目录的文件列出来，并读出 README.md 的前200字"))