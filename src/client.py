import os
import platform
import sys
from fastmcp.client import Client

# 서버 주소를 설정합니다. server.py와 같은 컴퓨터에서 실행하면 이 주소를 사용합니다.
SERVER_URL = "http://127.0.0.1:8000"


def clear_screen():
    """터미널 화면을 지우는 함수"""
    command = "cls" if platform.system() == "Windows" else "clear"
    os.system(command)


def print_welcome_message():
    """게임 시작 시 환영 메시지와 사용법을 출력합니다."""
    print("===================================")
    print("      Gomoku Game Client       ")
    print("===================================")
    print("\n명령어 안내:")
    print("  - 돌 놓기: 'x y' (예: '7 7')")
    print("  - 게임 재시작: 'restart'")
    print("  - 게임 종료: 'quit' 또는 'exit'")
    print("\n게임을 시작합니다...\n")
    input("서버가 실행 중인지 확인 후, Enter 키를 눌러주세요...")


def main():
    """메인 게임 루프를 실행하는 함수"""
    try:
        # FastMCP 클라이언트를 생성하여 서버에 연결합니다.
        client = Client(SERVER_URL)
        print(f"서버 {SERVER_URL}에 연결되었습니다.")
    except Exception as e:
        print(f"오류: 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        print(f"에러 상세: {e}")
        sys.exit(1)

    print_welcome_message()

    while True:
        try:
            clear_screen()

            # 서버로부터 현재 보드 상태를 시각화한 문자열을 받아옵니다.
            board_visualization = client.visualize()
            print(board_visualization)
            print("-" * (15 * 3 + 3))  # 보드와 정보란을 구분하는 선

            # 서버로부터 현재 게임 상태(GomokuState)를 받아옵니다.
            state = client.get_state()

            # 게임 상태에 따라 메시지를 출력합니다.
            if "WIN" in state.turn:
                print(f"🎉 게임 종료! {state.turn.replace('_', ' ')}! 🎉")
                print("새 게임을 시작하려면 'restart'를 입력하세요.")
            else:
                print(f"현재 턴: {state.turn} (●: BLACK, ○: WHITE)")

            # 사용자로부터 입력을 받습니다.
            user_input = input("명령을 입력하세요 > ").lower().strip()

            if user_input in ["quit", "exit"]:
                print("게임을 종료합니다.")
                break

            if user_input == "restart":
                client.restart()
                print("게임을 재시작했습니다.")
                input("계속하려면 Enter를 누르세요...")
                continue

            # 좌표 입력 처리 (예: "7 7")
            parts = user_input.split()
            if len(parts) == 2:
                x_str, y_str = parts
                if x_str.isdigit() and y_str.isdigit():
                    x, y = int(x_str), int(y_str)
                    # 서버의 set_stone 함수를 호출하여 돌을 놓습니다.
                    client.set_stone(x=x, y=y)
                else:
                    print("오류: 좌표는 숫자로 입력해야 합니다.")
                    input("계속하려면 Enter를 누르세요...")
            else:
                print(
                    f"오류: '{user_input}'는 잘못된 명령어입니다. (예: '7 7', 'restart')"
                )
                input("계속하려면 Enter를 누르세요...")

        except Exception as e:
            # 서버에서 발생한 오류(예: 이미 돌이 있는 곳에 놓는 경우)를 처리합니다.
            print(f"\n오류가 발생했습니다: {e}")
            input("계속하려면 Enter를 누르세요...")


if __name__ == "__main__":
    main()
