from fastmcp import FastMCP
from game.gomoku import Gomoku
from schema import GomokuState, TurnTypeAll

mcp_server = FastMCP(name="Gomoku MCP Server")


def get_mcp_server():
    global mcp_server
    return mcp_server


gomoku_game = Gomoku()


@mcp_server.tool
def restart() -> GomokuState:
    """
    🔄 Resets the game to its initial state.

    Use this when starting a completely new game. This clears the board of all stones
    and resets the move history. After calling this, BLACK will have the first move.

    Returns:
        GomokuState: The fresh state of the newly started game.
    """
    gomoku_game.restart()
    return gomoku_game.get_state()


@mcp_server.tool
def visualize() -> str:
    """
    👁️ Returns a text-based visual representation of the current game board.

    **IMPORTANT: Call this BEFORE making moves to see the current board layout.**

    This shows you where all the stones are placed in an easy-to-read grid format.
    Use this to understand the current game situation before deciding your next move.

    Returns:
        str: A string depicting the board with ● for BLACK stones, ○ for WHITE stones,
             and + for empty intersections.
    """
    return gomoku_game.visualize_board()


@mcp_server.tool
def get_state() -> GomokuState:
    """
    📊 Retrieves the complete current state of the game.

    **IMPORTANT: Call this FIRST to understand the current game before making any move.**

    This provides structured data about:
    - The board layout (15x15 grid)
    - Whose turn it is (BLACK or WHITE)
    - All stones that have been played
    - Game status (ongoing, won, draw)

    Returns:
        GomokuState: An object containing all information about the current game state.
    """
    return gomoku_game.get_state()


@mcp_server.tool
def set_stone(x: int, y: int, turn: str) -> GomokuState:
    """
    🎯 Places a stone for the specified player at the specified coordinates.

    **Call this AFTER analyzing the board with get_state() or visualize().**

    Args:
        x (int): The horizontal coordinate (0-14, left to right) where to place the stone.
        y (int): The vertical coordinate (0-14, top to bottom) where to place the stone.
        turn (str): The player making the move - must be "BLACK" or "WHITE".

    Returns:
        GomokuState: The updated game state after the move.

    Raises:
        ValueError: If the move is invalid because:
                    - The cell is already occupied
                    - Coordinates are out of bounds (not 0-14)
                    - It's not the specified player's turn
                    - The game is already over

    Example:
        set_stone(7, 7, "BLACK")  # Places a black stone at the center
    """
    return gomoku_game.set_stone(x, y, turn)


@mcp_server.tool
def get_valid_moves() -> list[tuple[int, int]]:
    """
    ✅ Provides a list of all valid (empty) positions where a stone can be placed.

    **RECOMMENDED: Call this after get_state() to see your options.**

    This helps you identify all possible next moves without trying invalid placements.
    Use this to narrow down your strategic choices to only legal moves.

    Returns:
        list[tuple[int, int]]: A list of (x, y) coordinate tuples for each empty cell.
                                Returns an empty list if the board is full.
    """
    return gomoku_game.get_valid_moves()


@mcp_server.tool
def get_history() -> list[GomokuState]:
    """
    📜 Returns a chronological list of all game states from the beginning.

    This can be used to:
    - Review the game's progression
    - Analyze past moves and strategies
    - Understand how the current position developed

    Each state in the list represents the board after one move.

    Returns:
        list[GomokuState]: A list of game state objects, one for each turn taken.
    """
    return gomoku_game.get_history()


@mcp_server.tool
def get_turn() -> TurnTypeAll:
    """
    🎲 Gets the current turn status.

    Returns one of:
    - "BLACK": It's Black's turn to move
    - "WHITE": It's White's turn to move
    - "BLACK_WIN": Black has won the game
    - "WHITE_WIN": White has won the game
    - "DRAW": The game ended in a draw (board full, no winner)

    Returns:
        TurnTypeAll: A string indicating whose turn it is or if the game has ended.
    """
    return gomoku_game.get_turn()


@mcp_server.tool
def get_rules() -> str:
    """
    📖 Returns the complete rules of the Gomoku game.

    Call this if you need a refresher on how Gomoku works.

    Returns:
        str: A detailed explanation of Gomoku rules and objectives.
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
    
    Strategic Tips:
    - Control the center early in the game
    - Look for opportunities to create multiple threats
    - Always consider both offensive and defensive moves
    - Block opponent's potential five-in-a-row sequences
    """

    return rules


if __name__ == "__main__":

    mcp_server.run()
