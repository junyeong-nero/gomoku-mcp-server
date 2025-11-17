USER_PROMPT = """It is now {turn}'s turn.

Follow these steps:
1. Call get_state() or visualize() to see the current board
2. Call get_valid_moves() to see available positions
3. Analyze the board and decide on your best move
4. Call set_stone(x, y, "{turn}") to make your move
5. Explain your strategic reasoning

Remember: You must actually CALL the tools, not just describe what you would do.
"""
