import os
import sys
import json
import asyncio
import requests

from openai import OpenAI

from mcp.server import get_mcp_server
from mcp.client import get_mcp_client
from schema import GomokuState
from utils import *

# --- 설정 ---
API_URL = "http://127.0.0.1:8000/api/state"

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


def send_state(state_data: dict):
    """현재 게임 상태를 FastAPI 서버로 POST"""
    try:
        response = requests.post(API_URL, json=state_data)
        response.raise_for_status()
        print("✅ 상태 업데이트 성공!")
        print("서버 응답:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"❌ 상태 업데이트 실패: {e}")
        if e.response:
            print("서버 응답 내용:", e.response.text)


async def run_gomoku_agent():
    """OpenRouter와 FastMCP를 사용하여 오목 게임을 플레이하는 에이전트"""

    mcp_client = get_mcp_client()
    print(f"✅ Gomoku 서버 프로세스를 생성했습니다.")

    async with mcp_client:

        print(f"✅ Gomoku 웹 서버를 생성했습니다.")

        # MCP 도구 목록 가져오기
        mcp_tools_raw = await mcp_client.list_tools()
        gomoku_tools = [to_openrouter_schema(tool) for tool in mcp_tools_raw]

        print("\n" + "=" * 60)
        print("🔧 OpenAI 형식으로 변환된 도구 목록:")
        print("=" * 60)
        for i, tool in enumerate(gomoku_tools, 1):
            print(f"\n[도구 {i}]")
            print(json.dumps(tool, indent=2, ensure_ascii=False))
        print("=" * 60)

        print("\n==============================================")
        print(f"   Gomoku AI Agent (Model: {MODEL_NAME})   ")
        print("==============================================")
        print("오목 게임에 대한 명령을 자연어로 입력하세요.")
        print("예: '게임 시작해줘', '지금 보드 상태 보여줘', '7, 7에 돌을 놔줘'")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.")

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that plays a game of Gomoku using the provided tools.",
            }
        ]

        while True:
            prompt = await asyncio.get_event_loop().run_in_executor(
                None, input, "\n👤 You: "
            )

            if prompt.lower() in ["quit", "exit"]:
                print("🤖 Agent: 게임을 종료합니다.")
                break

            messages.append({"role": "user", "content": prompt})

            try:
                # 첫 번째 요청
                response = openrouter_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=gomoku_tools,
                    tool_choice="auto",
                )

                if not response or not response.choices:
                    print("❌ API 응답이 비어있습니다.")
                    messages.pop()
                    continue

                response_message = response.choices[0].message

                # --- 🧩 Tool 호출 시 ---
                if response_message.tool_calls:
                    messages.append(response_message)

                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        print(f"⚡️ Calling function: {function_name}({function_args})")

                        try:
                            # MCP Tool 실행
                            function_response = await mcp_client.call_tool(
                                function_name, function_args
                            )

                            try:
                                # get_state 결과 가져오기
                                state_result = await mcp_client.call_tool("get_state")
                                json_string = state_result.content[0].text
                                state_data = GomokuState.model_validate_json(
                                    json_string
                                )
                                send_state(state_data.model_dump())
                            except Exception as e:
                                print(f"⚠️ 상태 전송 실패: {e}")

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

                    # 두 번째 요청
                    second_response = openrouter_client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                    )

                    if not second_response or not second_response.choices:
                        print("❌ 두 번째 API 응답이 비어있습니다.")
                        continue

                    final_response = second_response.choices[0].message.content
                    if final_response:
                        messages.append(
                            {"role": "assistant", "content": final_response}
                        )
                        print(f"🤖 Agent: {final_response}")

                # --- 일반 대화 응답 ---
                else:
                    final_response = response_message.content
                    messages.append({"role": "assistant", "content": final_response})
                    print(f"🤖 Agent: {final_response}")

            except Exception as e:
                print(f"❌ API 호출 중 오류 발생: {e}")
                import traceback

                traceback.print_exc()
                if messages and messages[-1]["role"] == "user":
                    messages.pop()


if __name__ == "__main__":
    asyncio.run(run_gomoku_agent())
