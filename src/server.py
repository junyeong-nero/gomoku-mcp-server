from fastmcp import FastMCP
from gomoku import Gomoku
from schema import GomokuState

mcp = FastMCP(name="Gomoku MCP Server")

gomoku_game = Gomoku()


@mcp.tool
def restart() -> GomokuState:
    """Restarts the gomoku game."""
    gomoku_game.restart()
    return gomoku_game.get_state()


@mcp.tool
def get_state() -> GomokuState:
    """Gets the current state of the gomoku game."""
    return gomoku_game.get_state()


@mcp.tool
def set_stone(x: int, y: int) -> GomokuState:
    """Sets a stone on the board."""
    return gomoku_game.set_stone(x, y)


@mcp.tool
def get_history() -> list[GomokuState]:
    """Gets the history of the gomoku game."""
    return gomoku_game.get_history()


if __name__ == "__main__":
    mcp.run()
