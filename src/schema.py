from pydantic import BaseModel, Field
from typing import Literal, List, Optional

PLAYER_TURNS = ("BLACK", "WHITE")
WIN_TURNS = tuple(f"{p}_WIN" for p in PLAYER_TURNS)

TurnType = Literal[*PLAYER_TURNS]
TurnTypeWin = Literal[*WIN_TURNS]
TurnTypeAll = Literal[*PLAYER_TURNS, *WIN_TURNS]

WIDTH, HEIGHT = 15, 15


class Stone(BaseModel):
    x: int = Field(..., ge=0, lt=WIDTH)
    y: int = Field(..., ge=0, lt=HEIGHT)
    type: TurnType


class GomokuState(BaseModel):
    turn: TurnTypeAll = Field(default="BLACK")
    stones: List[Stone] = Field(default_factory=list)
    board: List[List[Optional[TurnType]]] = Field(
        default_factory=lambda: [[None for _ in range(WIDTH)] for _ in range(HEIGHT)]
    )
