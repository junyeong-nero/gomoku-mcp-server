import os
import sys
import json
import asyncio
from typing import Any
from openai import OpenAI

from fastmcp.client import Client

# --- 설정 ---

# 1. OpenRouter API 키 설정
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("❌ 오류: OPENROUTER_API_KEY 환경 변수가 설정되지 않았습니다.")
    sys.exit(1)

# 2. OpenRouter 클라이언트 생성
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# 3. 사용할 모델 이름 설정
MODEL_NAME = "google/gemini-2.5-flash"


def to_openai_schema(tool) -> dict:
    """
    FastMCP 도구를 OpenAI/OpenRouter 형식으로 변환합니다.
    """
    raw_schema = (
        getattr(tool, "inputSchema", None)
        or getattr(tool, "input_schema", None)
        or getattr(tool, "parameters", None)
    )

    if raw_schema is None:
        schema: dict = {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        }

    elif isinstance(raw_schema, dict):
        schema = raw_schema

    elif hasattr(raw_schema, "model_json_schema"):
        schema = raw_schema.model_json_schema()

    elif isinstance(raw_schema, list):
        props, required = {}, []
        for p in raw_schema:
            props[p["name"]] = {
                "type": p["type"],
                "description": p.get("description", ""),
            }
            if p.get("required", True):
                required.append(p["name"])
        schema = {"type": "object", "properties": props}
        if required:
            schema["required"] = required

    else:
        schema = {"type": "object", "properties": {}, "additionalProperties": True}

    schema.setdefault("type", "object")
    schema.setdefault("properties", {})
    if "required" not in schema:
        schema["required"] = list(schema["properties"].keys())

    # OpenRouter가 기대하는 형식으로 반환
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": getattr(tool, "description", ""),
            "parameters": schema,
        },
    }


async def run_gomoku_agent():
    """OpenRouter와 FastMCP를 사용하여 오목 게임을 플레이하는 에이전트"""
    try:
        mcp_client = Client("src/server.py")
        print(f"✅ Gomoku 서버 프로세스를 생성했습니다.")

    except Exception as e:
        print(f"❌ 오류: Gomoku 서버 프로세스를 시작할 수 없습니다.")
        print(f"   에러 상세: {e}")
        return

    # async with 컨텍스트 매니저로 클라이언트 연결
    async with mcp_client:
        # FastMCP 클라이언트에서 도구 목록을 가져옵니다.
        mcp_tools = await mcp_client.list_tools()

        # MCP 형식을 OpenAI/OpenRouter 형식으로 변환
        gomoku_tools = [to_openai_schema(tool) for tool in mcp_tools]

        print("✅ Gomoku 서버로부터 사용 가능한 함수(Tools) 목록을 가져왔습니다.")
        print(f"   변환된 도구 개수: {len(gomoku_tools)}")

    # async with 컨텍스트 매니저로 클라이언트 연결
    async with mcp_client:
        # FastMCP 클라이언트에서 OpenAI 호환 형식의 tool 목록을 가져옵니다.
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
                            function_to_call = getattr(mcp_client, function_name)
                            # await를 사용하여 비동기 함수 호출
                            function_response = await function_to_call(**function_args)
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
