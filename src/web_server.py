from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from schema import GomokuState
import uvicorn


class WebManager:
    def __init__(self) -> None:
        self.app = FastAPI()
        self.current_state: GomokuState | None = GomokuState()  # 최신 상태를 저장
        self.setup()

    def setup(self):
        @self.app.get("/api/state")
        async def get_state():
            """현재 Gomoku 게임 상태를 반환하는 API 엔드포인트"""
            if self.current_state is None:
                return JSONResponse(
                    content={"error": "No game state available"}, status_code=404
                )
            return JSONResponse(content=self.current_state.model_dump())

        @self.app.post("/api/state")
        async def post_state(request: Request):
            """외부에서 Gomoku 상태를 업데이트하는 엔드포인트"""
            try:
                data = await request.json()
                state = GomokuState.model_validate(data)
                self.current_state = state
                return JSONResponse(
                    content={"message": "Game state updated successfully"}
                )
            except Exception as e:
                import traceback

                traceback.print_exc()
                return JSONResponse(content={"error": str(e)}, status_code=400)

        @self.app.get("/", response_class=HTMLResponse)
        async def get_homepage():
            """메인 HTML 페이지 렌더링"""
            html_content = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Gomoku Live Board</title>
                <style>
                    :root {
                        --board-size: 15;
                        --cell-size: 40px;
                        --board-bg-color: #e3c16f;
                        --line-color: #5a4f41;
                        --stone-size-ratio: 0.85;
                    }
                    body {
                        background-color: #282c34;
                        color: #abb2bf;
                        font-family: 'Consolas', 'Monaco', monospace;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        padding: 20px;
                    }
                    h1 { color: #61afef; margin: 10px 0; }
                    #turn-info { color: #e5c07b; font-size: 1.5em; margin: 10px 0; }
                    #board-container {
                        padding: calc(var(--cell-size) / 2);
                        background-color: var(--board-bg-color);
                        border-radius: 8px;
                        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
                        margin: 20px 0;
                    }
                    #gomoku-board {
                        display: grid;
                        grid-template-columns: repeat(var(--board-size), var(--cell-size));
                        grid-template-rows: repeat(var(--board-size), var(--cell-size));
                        width: calc(var(--board-size) * var(--cell-size));
                        height: calc(var(--board-size) * var(--cell-size));
                        background-color: var(--board-bg-color);
                        border: 2px solid var(--line-color);
                        background-image: 
                            repeating-linear-gradient(to right, transparent, transparent calc(var(--cell-size) - 1px), var(--line-color) calc(var(--cell-size) - 1px), var(--line-color) var(--cell-size)),
                            repeating-linear-gradient(to bottom, transparent, transparent calc(var(--cell-size) - 1px), var(--line-color) calc(var(--cell-size) - 1px), var(--line-color) var(--cell-size));
                        background-position: center center;
                    }
                    .cell {
                        position: relative;
                        width: var(--cell-size);
                        height: var(--cell-size);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }
                    .stone {
                        position: absolute;
                        width: calc(var(--cell-size) * var(--stone-size-ratio));
                        height: calc(var(--cell-size) * var(--stone-size-ratio));
                        border-radius: 50%;
                        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
                        transform: translate(-50%, -50%);
                        top: 50%;
                        left: 50%;
                    }
                    .stone.black { background: radial-gradient(circle at 35% 35%, #555, #000); }
                    .stone.white { background: radial-gradient(circle at 35% 35%, #fff, #ccc); }
                    #debug {
                        color: #98c379;
                        font-size: 0.9em;
                        margin: 10px 0;
                        padding: 10px;
                        background-color: #21252b;
                        border-radius: 4px;
                    }
                    #raw-state {
                        background-color: #21252b;
                        border: 1px solid #4b5263;
                        border-radius: 4px;
                        padding: 15px;
                        margin-top: 10px;
                        max-height: 400px;
                        overflow-y: auto;
                        font-size: 0.85em;
                        line-height: 1.4;
                    }
                    .error { color: #e06c75; }
                </style>
            </head>
            <body>
                <h1>Gomoku Live Board</h1>
                <h2 id="turn-info">Connecting...</h2>
                <div id="board-container"><div id="gomoku-board"></div></div>
                <div id="debug">Initializing...</div>
                <div id="raw-state"><pre id="state-json">Loading...</pre></div>
                <script>
                    const boardElement = document.getElementById("gomoku-board");
                    const turnInfoElement = document.getElementById("turn-info");
                    const debugElement = document.getElementById("debug");
                    const stateJsonElement = document.getElementById("state-json");

                    function initializeBoard(size) {
                        boardElement.innerHTML = '';
                        document.documentElement.style.setProperty('--board-size', size);
                        for (let r = 0; r < size; r++) {
                            for (let c = 0; c < size; c++) {
                                const cellElement = document.createElement('div');
                                cellElement.classList.add('cell');
                                cellElement.id = `cell-${r}-${c}`;
                                boardElement.appendChild(cellElement);
                            }
                        }
                    }

                    function updateBoard(gameState) {
                        try {
                            stateJsonElement.textContent = JSON.stringify(gameState, null, 2);
                            if (gameState.error) throw new Error(gameState.error);
                            const { turn, board } = gameState;
                            const height = board.length, width = board[0].length;
                            if (boardElement.children.length !== height * width) initializeBoard(width);
                            turnInfoElement.textContent = `Turn: ${turn}`;
                            debugElement.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
                            for (let r = 0; r < height; r++) {
                                for (let c = 0; c < width; c++) {
                                    const cell = document.getElementById(`cell-${r}-${c}`);
                                    if (!cell) continue;
                                    const existingStone = cell.querySelector('.stone');
                                    if (existingStone) existingStone.remove();
                                    const stoneType = board[r][c];
                                    if (stoneType) {
                                        const stone = document.createElement('div');
                                        stone.classList.add('stone', stoneType.toLowerCase());
                                        cell.appendChild(stone);
                                    }
                                }
                            }
                        } catch (e) {
                            turnInfoElement.textContent = "Error: " + e.message;
                            turnInfoElement.className = 'error';
                        }
                    }

                    async function fetchState() {
                        try {
                            const res = await fetch('/api/state');
                            const data = await res.json();
                            updateBoard(data);
                        } catch (e) {
                            debugElement.textContent = "Fetch error: " + e.message;
                        }
                    }

                    fetchState();
                    setInterval(fetchState, 1000);
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

    def run_server(self, host="0.0.0.0", port=8000):
        """Uvicorn 서버 실행"""
        print(f"서버 시작: http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


if __name__ == "__main__":
    manager = WebManager()
    manager.run_server()
