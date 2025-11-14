import pytest
from game.gomoku import Gomoku
from schema import GomokuState, Stone


def test_set_stone():
    gomoku = Gomoku()
    state = gomoku.set_stone(7, 7)
    print(gomoku.visualize_board())
