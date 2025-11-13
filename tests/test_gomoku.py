import pytest
from gomoku import Gomoku
from schema import GomokuState, Stone


def test_initial_state():
    gomoku = Gomoku()
    state = gomoku.get_state()
    assert state.turn == "BLACK"
    assert len(state.stones) == 0
    assert all(all(cell is None for cell in row) for row in state.board)


def test_set_stone():
    gomoku = Gomoku()
    state = gomoku.set_stone(7, 7)
    assert state.turn == "WHITE"
    assert len(state.stones) == 1
    assert state.stones[0] == Stone(x=7, y=7, type="BLACK")
    assert state.board[7][7] == "BLACK"


def test_set_stone_occupied():
    gomoku = Gomoku()
    gomoku.set_stone(7, 7)
    with pytest.raises(ValueError, match="Cell is already occupied"):
        gomoku.set_stone(7, 7)


def test_set_stone_out_of_bounds():
    gomoku = Gomoku()
    with pytest.raises(ValueError, match="Coordinates out of bounds"):
        gomoku.set_stone(15, 7)
    with pytest.raises(ValueError, match="Coordinates out of bounds"):
        gomoku.set_stone(7, 15)


def test_win_horizontal():
    gomoku = Gomoku()
    for i in range(4):
        gomoku.set_stone(i, 0)  # Black
        gomoku.set_stone(i, 1)  # White
    state = gomoku.set_stone(4, 0)  # Black wins
    assert state.turn == "BLACK_WIN"


def test_win_vertical():
    gomoku = Gomoku()
    for i in range(4):
        gomoku.set_stone(0, i)  # Black
        gomoku.set_stone(1, i)  # White
    state = gomoku.set_stone(0, 4)  # Black wins
    assert state.turn == "BLACK_WIN"


def test_win_diagonal_down():
    gomoku = Gomoku()
    for i in range(4):
        gomoku.set_stone(i, i)  # Black
        gomoku.set_stone(i, i + 1)  # White
    state = gomoku.set_stone(4, 4)  # Black wins
    assert state.turn == "BLACK_WIN"


def test_win_diagonal_up():
    gomoku = Gomoku()
    for i in range(4):
        gomoku.set_stone(i, 4 - i)  # Black
        gomoku.set_stone(i, 5 - i)  # White
    state = gomoku.set_stone(4, 0)  # Black wins
    assert state.turn == "BLACK_WIN"


def test_restart():
    gomoku = Gomoku()
    gomoku.set_stone(7, 7)
    gomoku.restart()
    state = gomoku.get_state()
    assert state.turn == "BLACK"
    assert len(state.stones) == 0
    assert all(all(cell is None for cell in row) for row in state.board)


def test_get_history():
    gomoku = Gomoku()
    history = gomoku.get_history()
    assert len(history) == 1
    gomoku.set_stone(7, 7)
    history = gomoku.get_history()
    assert len(history) == 2
    assert history[0].turn == "BLACK"
    assert history[1].turn == "WHITE"


def test_set_stone_after_win():
    gomoku = Gomoku()
    for i in range(4):
        gomoku.set_stone(i, 0)
        gomoku.set_stone(i, 1)
    gomoku.set_stone(4, 0)  # Black wins
    with pytest.raises(ValueError, match="Game is already over"):
        gomoku.set_stone(5, 0)
