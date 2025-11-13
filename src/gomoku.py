from schema import GomokuState, Stone, WIDTH, HEIGHT, TurnType


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
        stone_type = self._state.board[y][x]
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
