
# Install

```shell
uv sync
uv pip install -e .
```

# Run

```
uv run src/cli.py
uv run src/gui.py
```


# configure

```python
"mcp-gomoku": {
    "command": "uv",
    "args": [
        "--directory",
        "/Users/junyeong-nero/workspace/gomoku-mcp-server/",
        "run",
        "src/server.py"
    ]
}
```