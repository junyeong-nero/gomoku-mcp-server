from pydantic import BaseModel, Field
from typing import Literal, List, Optional

TurnType = Literal["WHITE", "BLACK"]
TurnTypeWin = Literal["WHITE_WIN", "BLACK_WIN"]
TurnTypeAll = Literal[TurnType, TurnTypeWin]

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
