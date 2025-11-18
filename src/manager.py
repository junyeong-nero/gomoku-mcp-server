import json


from game.gomoku import GomokuState
from utils import *
from prompts.system_prompt import SYSTEM_PROMPT
from prompts.user_prompt import USER_PROMPT
from models import AVAILABLE_MODELS


class GameManager:
    def __init__(self, mcp_client, openrouter_client):
        self.current_state: GomokuState = GomokuState()
        self.mcp_client = mcp_client
        self.openrouter_client = openrouter_client
        self.gomoku_tools = []
        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]
        self.current_model = AVAILABLE_MODELS[0]["id"]
        self.initialize_mcp()

    async def initialize_mcp(self):
        """MCP 클라이언트 초기화"""
        await self.mcp_client.__aenter__()
        mcp_tools_raw = await self.mcp_client.list_tools()
        self.gomoku_tools = [to_openrouter_schema(tool) for tool in mcp_tools_raw]
        print("✅ MCP 클라이언트 초기화 완료")

    async def update_state(self):
        try:
            state_result = await self.mcp_client.call_tool("get_state")
            json_string = state_result.content[0].text
            self.current_state = GomokuState.model_validate_json(json_string)
        except Exception as e:
            print(f"⚠️ 상태 업데이트 실패: {e}")
        return self.current_state

    async def set_stone(self, x, y):
        """현재 턴의 플레이어가 돌을 놓음"""
        current_turn = self.current_state.turn
        await self.mcp_client.call_tool(
            "set_stone", {"x": x, "y": y, "turn": current_turn}
        )
        return await self.update_state()

    async def process_ai_turn(self) -> dict:
        """AI가 상대방 입장에서 수를 둠"""
        current_turn = self.current_state.turn

        # USER_PROMPT에 현재 턴 정보 삽입
        user_prompt = USER_PROMPT.format(turn=current_turn)
        self.messages.append({"role": "user", "content": user_prompt})

        try:
            # 반복적으로 도구를 호출하도록 루프 사용
            max_iterations = 10  # 무한 루프 방지
            iteration = 0

            while iteration < max_iterations:
                response = self.openrouter_client.chat.completions.create(
                    model=self.current_model,
                    messages=self.messages,
                    tools=self.gomoku_tools,
                    tool_choice="auto",
                )

                if not response or not response.choices:
                    return {"error": "API 응답이 비어있습니다."}

                response_message = response.choices[0].message

                # Tool 호출 시
                if response_message.tool_calls:
                    self.messages.append(response_message)
                    tool_results = []

                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        try:
                            # MCP Tool 실행
                            function_response = await self.mcp_client.call_tool(
                                function_name, function_args
                            )

                            tool_results.append(
                                {
                                    "name": function_name,
                                    "args": function_args,
                                    "result": str(function_response),
                                }
                            )

                            await self.update_state()

                        except Exception as e:
                            function_response = f"Error executing function: {e}"
                            tool_results.append(
                                {
                                    "name": function_name,
                                    "args": function_args,
                                    "error": str(e),
                                }
                            )

                        self.messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": str(function_response),
                            }
                        )

                    # 다음 iteration으로
                    iteration += 1
                    continue

                # 일반 대화 응답 (tool_calls 없음)
                else:
                    final_response = response_message.content
                    self.messages.append(
                        {"role": "assistant", "content": final_response}
                    )

                    return {
                        "response": final_response,
                        "state": self.current_state.model_dump(),
                    }

            # max_iterations 초과
            return {"error": "최대 반복 횟수를 초과했습니다."}

        except Exception as e:
            print(f"❌ API 호출 중 오류 발생: {e}")
            import traceback

            traceback.print_exc()
            if self.messages and self.messages[-1]["role"] == "user":
                self.messages.pop()
            return {"error": str(e)}

    async def process_message(self, user_message: str, model: str) -> dict:
        """사용자 메시지를 처리하고 AI 응답 반환 (채팅용)"""
        self.current_model = model
        self.messages.append({"role": "user", "content": user_message})

        try:
            # 첫 번째 요청
            response = self.openrouter_client.chat.completions.create(
                model=self.current_model,
                messages=self.messages,
                tools=self.gomoku_tools,
                tool_choice="required",
            )

            if not response or not response.choices:
                return {"error": "API 응답이 비어있습니다."}

            response_message = response.choices[0].message

            # Tool 호출 시
            if response_message.tool_calls:
                self.messages.append(response_message)
                tool_results = []

                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    try:
                        # MCP Tool 실행
                        function_response = await self.mcp_client.call_tool(
                            function_name, function_args
                        )

                        tool_results.append(
                            {
                                "name": function_name,
                                "args": function_args,
                                "result": str(function_response),
                            }
                        )

                        await self.update_state()

                    except Exception as e:
                        function_response = f"Error executing function: {e}"
                        tool_results.append(
                            {
                                "name": function_name,
                                "args": function_args,
                                "error": str(e),
                            }
                        )

                    self.messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": str(function_response),
                        }
                    )

                # 두 번째 요청
                second_response = self.openrouter_client.chat.completions.create(
                    model=self.current_model,
                    messages=self.messages,
                )

                if second_response and second_response.choices:
                    final_response = second_response.choices[0].message.content
                    self.messages.append(
                        {"role": "assistant", "content": final_response}
                    )

                    return {
                        "response": final_response,
                        "tool_calls": tool_results,
                        "state": self.current_state.model_dump(),
                    }

            # 일반 대화 응답
            else:
                final_response = response_message.content
                self.messages.append({"role": "assistant", "content": final_response})

                return {
                    "response": final_response,
                    "state": self.current_state.model_dump(),
                }

        except Exception as e:
            print(f"❌ API 호출 중 오류 발생: {e}")
            import traceback

            traceback.print_exc()
            if self.messages and self.messages[-1]["role"] == "user":
                self.messages.pop()
            return {"error": str(e)}
