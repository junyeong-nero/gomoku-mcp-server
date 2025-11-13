import requests
from schema import GomokuState

API_URL = "http://127.0.0.1:8000/api/state"


def create_sample_gomoku_state():
    WIDTH, HEIGHT = 15, 15
    board = [[None for _ in range(WIDTH)] for _ in range(HEIGHT)]
    stones = []

    def place_stone(y, x, stone_type):
        if 0 <= y < HEIGHT and 0 <= x < WIDTH:
            board[y][x] = stone_type
            # 'type' 필드명을 사용하는 것이 올바른 코드입니다.
            stones.append({"y": y, "x": x, "type": stone_type})

    # 예시 돌 배치
    place_stone(7, 7, "BLACK")
    place_stone(6, 7, "WHITE")
    place_stone(7, 8, "BLACK")

    game_state = {
        "turn": "WHITE",
        "board": board,
        "stones": stones,
    }
    return game_state


def send_state(state_data: dict):
    try:
        response = requests.post(API_URL, json=state_data)
        response.raise_for_status()
        print("✅ 상태 업데이트 성공!")
        print("서버 응답:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"❌ 상태 업데이트 실패: {e}")
        if e.response:
            print("서버 응답 내용:", e.response.text)


if __name__ == "__main__":
    sample_state = create_sample_gomoku_state()
    send_state(sample_state)
