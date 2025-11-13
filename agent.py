import os
import sys
import json
import asyncio
from typing import Any
from openai import OpenAI
import multiprocessing

from server import get_mcp_server
from client import get_mcp_client
from web import WebManager

# --- 설정 ---

# 1. OpenRouter API 키 설정
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("❌ 오류: OPENROUTER_API_KEY 환경 변수가 설정되지 않았습니다.")
    sys.exit(1)

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

MODEL_NAME = "google/gemini-2.5-flash"


def run_web_server(client):

    web_server = WebManager(client)
    web_server.run_server()
    # server_process = multiprocessing.Process(
    #     target=web_server.run_server, args=("127.0.0.1", 8000)
    # )
    # server_process.daemon = True
    # server_process.start()
    # print(f"서버 프로세스 (PID: {server_process.pid})가 백그라운드에서 시작되었습니다.")


async def run_gomoku_agent():
    """OpenRouter와 FastMCP를 사용하여 오목 게임을 플레이하는 에이전트"""

    mcp_client = get_mcp_client()
    print(f"✅ Gomoku 서버 프로세스를 생성했습니다.")

    async with mcp_client:

        run_web_server(mcp_client)
        print(f"✅ Gomoku 웹 서버를 생성했습니다.")

        gomoku_tools = await mcp_client.list_tools()
        print("✅ Gomoku 서버로부터 사용 가능한 함수(Tools) 목록을 가져왔습니다.")

        print("\n==============================================")
        print(f"   Gomoku AI Agent (Model: {MODEL_NAME})   ")
        print("==============================================")
        print("오목 게임에 대한 명령을 자연어로 입력하세요.")
        print("예: '게임 시작해줘', '지금 보드 상태 보여줘', '7, 7에 돌을 놔줘'")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.")

        # 대화 기록을 관리하는 리스트
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that plays a game of Gomoku using the provided tools.",
            }
        ]

        while True:
            # asyncio-compatible input
            prompt = await asyncio.get_event_loop().run_in_executor(
                None, input, "\n👤 You: "
            )

            if prompt.lower() in ["quit", "exit"]:
                print("🤖 Agent: 게임을 종료합니다.")
                break

            messages.append({"role": "user", "content": prompt})

            try:
                # 1. OpenRouter에 첫 번째 요청을 보냅니다.
                response = openrouter_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=gomoku_tools,
                    tool_choice="auto",
                )

                # 응답 유효성 검사
                if not response or not response.choices or len(response.choices) == 0:
                    print(f"❌ API 응답이 비어있습니다. 응답: {response}")
                    messages.pop()
                    continue

                response_message = response.choices[0].message

                # 2. 모델이 함수 호출을 결정했는지 확인합니다.
                if response_message.tool_calls:
                    messages.append(response_message)

                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        print(f"⚡️ Calling function: {function_name}({function_args})")

                        try:
                            function_response = mcp_client.call_tool(
                                function_name, function_args
                            )
                            # function_to_call = getattr(mcp_client, function_name)
                            # function_response = await function_to_call(**function_args)
                        except Exception as e:
                            print(f"    - Function call error: {e}")
                            function_response = f"Error executing function: {e}"

                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": str(function_response),
                            }
                        )

                    # 3. 함수 실행 결과를 포함하여 OpenRouter에 두 번째 요청을 보냅니다.
                    second_response = openrouter_client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                    )

                    # 두 번째 응답 유효성 검사
                    if (
                        not second_response
                        or not second_response.choices
                        or len(second_response.choices) == 0
                    ):
                        print(f"❌ 두 번째 API 응답이 비어있습니다.")
                        continue

                    final_response = second_response.choices[0].message.content

                    if not final_response:
                        print("❌ 응답 내용이 비어있습니다.")
                        continue

                    messages.append({"role": "assistant", "content": final_response})
                    print(f"🤖 Agent: {final_response}")

                else:
                    final_response = response_message.content
                    messages.append({"role": "assistant", "content": final_response})
                    print(f"🤖 Agent: {final_response}")

            except Exception as e:
                print(f"❌ API 호출 중 오류가 발생했습니다: {e}")
                print(f"   오류 타입: {type(e).__name__}")
                import traceback

                traceback.print_exc()
                if messages and messages[-1]["role"] == "user":
                    messages.pop()


if __name__ == "__main__":
    asyncio.run(run_gomoku_agent())
