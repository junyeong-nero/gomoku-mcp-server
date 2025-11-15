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
    """
    Resets the game to its initial state.

    This function clears the board of all stones and resets the move history.
    It should be called when a new game is desired.

    Returns:
        GomokuState: The fresh state of the newly started game.
    """
    gomoku_game.restart()
    return gomoku_game.get_state()


@mcp_server.tool
def visualize() -> str:
    """
    Returns a text-based representation of the current game board.

    This visualization is useful for understanding the current placement of stones
    and the overall game situation from a human-readable perspective.

    Returns:
        str: A string depicting the board with stones and empty intersections.
    """
    return gomoku_game.visualize_board()


@mcp_server.tool
def get_state() -> GomokuState:
    """
    Retrieves the complete current state of the game.

    The game state includes the board layout, whose turn it is (BLACK or WHITE),
    and a list of all stones that have been played.

    Returns:
        GomokuState: An object containing all information about the current game state.
    """
    return gomoku_game.get_state()


@mcp_server.tool
def set_stone(x: int, y: int) -> GomokuState:
    """
    Places a stone for the current player at the specified coordinates.

    Args:
        x (int): The horizontal coordinate (0-14) of the cell to place the stone on.
        y (int): The vertical coordinate (0-14) of the cell to place the stone on.

    Returns:
        GomokuState: The updated game state after the move.

    Raises:
        ValueError: If the move is invalid (e.g., cell is already occupied,
                    coordinates are out of bounds, or the game is already over).
    """
    return gomoku_game.set_stone(x, y)


@mcp_server.tool
def get_history() -> list[GomokuState]:
    """
    Returns a chronological list of all game states from the beginning.

    This can be used to review the game's progression or to analyze past moves.

    Returns:
        list[GomokuState]: A list of game state objects, one for each turn taken.
    """
    return gomoku_game.get_history()


@mcp_server.tool
def get_valid_moves() -> list[tuple[int, int]]:
    """
    Provides a list of all valid moves available on the current board.

    A valid move is any empty cell on the board. This tool helps in identifying
    all possible next actions without trying invalid placements.

    Returns:
        list[tuple[int, int]]: A list of (x, y) coordinate tuples for each empty cell.
    """

    return gomoku_game.get_valid_moves()


@mcp_server.tool
def get_rules() -> str:
    """
    Returns the rules of the Gomoku game.

    Returns:
        str: A string detailing the rules of Gomoku.
    """

    rules = """
    Gomoku (also known as Five in a Row) Rules:
    
    1. The game is played on a 15x15 grid.
    2. Two players, Black and White, take turns placing their stones on empty intersections.
    3. Black plays first.
    4. The objective is to be the first player to get an unbroken row of five stones
       horizontally, vertically, or diagonally.
    5. Once a stone is placed, it cannot be moved or removed.
    6. There are no special rules for 'three-three' or 'four-four' (free Gomoku).
    7. The game ends when a player achieves five in a row or the board is full (draw).
    """

    return rules


if __name__ == "__main__":

    mcp_server.run()
