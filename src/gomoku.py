from schema import GomokuState, Stone, WIDTH, HEIGHT, TurnType
from typing import Optional  # Optional 임포트 추가


class Gomoku:

    def __init__(self) -> None:
        self.restart()

    def restart(self):
        self._state = GomokuState()
        self._history: list[GomokuState] = [self._state.model_copy(deep=True)]

    def get_state(self) -> GomokuState:
        return self._state

    def set_stone(self, x: int, y: int) -> GomokuState:
        if "WIN" in self._state.turn:
            raise ValueError("Game is already over")
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
            raise ValueError("Coordinates out of bounds")
        if self._state.board[y][x] is not None:
            raise ValueError("Cell is already occupied")

        stone_type: TurnType = "BLACK" if self._state.turn == "BLACK" else "WHITE"
        stone = Stone(x=x, y=y, type=stone_type)
        self._state.stones.append(stone)
        self._state.board[y][x] = stone_type

        if self._check_win(x, y):
            self._state.turn = f"{stone_type}_WIN"
        else:
            self._state.turn = "WHITE" if self._state.turn == "BLACK" else "BLACK"

        self._history.append(self._state.model_copy(deep=True))
        return self._state

    def get_history(self) -> list[GomokuState]:
        return self._history

    def _check_win(self, x: int, y: int) -> bool:
        stone_type: Optional[TurnType] = self._state.board[y][x]
        if stone_type is None:
            return False

        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            count = 1
            # Check in the positive direction
            for i in range(1, 5):
                nx, ny = x + i * dx, y + i * dy
                if (
                    0 <= nx < WIDTH
                    and 0 <= ny < HEIGHT
                    and self._state.board[ny][nx] == stone_type
                ):
                    count += 1
                else:
                    break
            # Check in the negative direction
            for i in range(1, 5):
                nx, ny = x - i * dx, y - i * dy
                if (
                    0 <= nx < WIDTH
                    and 0 <= ny < HEIGHT
                    and self._state.board[ny][nx] == stone_type
                ):
                    count += 1
                else:
                    break
            if count >= 5:
                return True
        return False

    # --- 추가된 메서드 ---
    def visualize_board(self) -> str:
        """
        현재 게임 보드를 텍스트 형식의 문자열로 생성합니다.
        ●: 검은 돌
        ○: 흰 돌
        +: 빈 칸
        """
        # 각 상태에 맞는 심볼을 정의합니다.
        symbols = {
            "BLACK": "●",
            "WHITE": "○",
            None: "+",
        }

        # 최종 결과를 담을 문자열 리스트를 생성합니다.
        board_lines = []

        # 열 번호 헤더를 만듭니다 (e.g., "   0  1  2 ...")
        # 행 번호(예: '14 ')와 정렬을 맞추기 위해 앞부분에 공백을 추가합니다.
        header = "   " + " ".join(f"{i:<2}" for i in range(WIDTH))
        board_lines.append(header)

        # 각 행을 순회하며 문자열을 만듭니다.
        for y in range(HEIGHT):
            # 행 번호를 왼쪽에 추가하고, 두 자리로 정렬합니다.
            row_str = f"{y:>2} "

            # 해당 행의 각 칸을 순회합니다.
            for x in range(WIDTH):
                stone = self._state.board[y][x]
                # 심볼과 공백을 추가하여 정렬을 맞춥니다.
                row_str += symbols[stone] + "  "

            board_lines.append(row_str)

        # 모든 라인을 개행 문자로 합쳐 하나의 문자열로 반환합니다.
        return "\n".join(board_lines)
