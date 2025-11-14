from fastmcp import FastMCP
from game.gomoku import Gomoku
from schema import GomokuState

mcp_server = FastMCP(name="Gomoku MCP Server")


def get_mcp_server():
    global mcp_server
    return mcp_server


gomoku_game = Gomoku()


@mcp_server.tool
def restart() -> GomokuState:
    """Restarts the gomoku game."""
    gomoku_game.restart()
    return gomoku_game.get_state()


@mcp_server.tool
def visualize() -> str:
    """Visualize current state of the board"""
    return gomoku_game.visualize_board()


@mcp_server.tool
def get_state() -> GomokuState:
    """Gets the current state of the gomoku game."""
    return gomoku_game.get_state()


@mcp_server.tool
def set_stone(x: int, y: int) -> GomokuState:
    """Sets a stone on the board."""
    return gomoku_game.set_stone(x, y)


@mcp_server.tool
def get_history() -> list[GomokuState]:
    """Gets the history of the gomoku game."""
    return gomoku_game.get_history()


if __name__ == "__main__":
    mcp_server.run()
