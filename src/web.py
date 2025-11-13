from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from schema import GomokuState
import uvicorn


class WebManager:

    def __init__(self, client) -> None:
        self.mcp_client = client
        self.app = FastAPI()
        self.setup()

    def setup(self):
        @self.app.get("/api/state")
        async def get_state():
            """현재 Gomoku 게임 상태를 반환하는 API 엔드포인트"""
            try:
                async with self.mcp_client:
                    # mcp_client를 통해 'get_state' 함수를 호출
                    state = await self.mcp_client.call_tool("get_state")

                    # CallToolResult에서 원본 JSON 문자열을 추출
                    json_string = state.content[0].text
                    data = GomokuState.model_validate_json(json_string)

                    # Pydantic 모델을 dict로 변환하여 반환
                    return JSONResponse(content=data.model_dump())

            except Exception as e:
                error_message = f"Error communicating with Gomoku server: {e}"
                print(error_message)
                import traceback

                traceback.print_exc()
                return JSONResponse(content={"error": error_message}, status_code=500)

        @self.app.get("/", response_class=HTMLResponse)
        async def get_homepage():
            """메인 HTML 페이지를 렌더링합니다."""
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

                    h1 { 
                        color: #61afef; 
                        margin: 10px 0;
                    }
                    
                    #turn-info { 
                        color: #e5c07b; 
                        font-size: 1.5em;
                        margin: 10px 0;
                    }

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

                    .stone.black {
                        background: radial-gradient(circle at 35% 35%, #555, #000);
                    }

                    .stone.white {
                        background: radial-gradient(circle at 35% 35%, #fff, #ccc);
                    }

                    #info-container {
                        width: 100%;
                        max-width: 1000px;
                        margin-top: 20px;
                    }

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

                    #raw-state h3 {
                        color: #c678dd;
                        margin-top: 0;
                        margin-bottom: 10px;
                    }

                    #raw-state pre {
                        margin: 0;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        color: #abb2bf;
                    }

                    .error {
                        color: #e06c75;
                    }
                </style>
            </head>
            <body>
                <h1>Gomoku Live Board</h1>
                <h2 id="turn-info">Connecting...</h2>
                <div id="board-container">
                    <div id="gomoku-board"></div>
                </div>
                
                <div id="info-container">
                    <div id="debug">Initializing...</div>
                    <div id="raw-state">
                        <h3>Raw GomokuState</h3>
                        <pre id="state-json">Loading...</pre>
                    </div>
                </div>

                <script>
                    const boardElement = document.getElementById("gomoku-board");
                    const turnInfoElement = document.getElementById("turn-info");
                    const debugElement = document.getElementById("debug");
                    const stateJsonElement = document.getElementById("state-json");
                    
                    let updateInterval = null;

                    function initializeBoard(size) {
                        console.log(`Initializing board with size: ${size}`);
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
                        console.log("Received game state:", gameState);
                        
                        // Raw state를 JSON 형태로 표시
                        try {
                            stateJsonElement.textContent = JSON.stringify(gameState, null, 2);
                            stateJsonElement.className = '';
                        } catch (e) {
                            stateJsonElement.textContent = "Error formatting state: " + e.message;
                            stateJsonElement.className = 'error';
                        }
                        
                        // 에러 체크
                        if (gameState.error) {
                            turnInfoElement.textContent = "Error: " + gameState.error;
                            turnInfoElement.className = 'error';
                            debugElement.textContent = "Error: " + gameState.error;
                            debugElement.className = 'error';
                            return;
                        }
                        
                        const { turn, board, stones } = gameState;
                        
                        // board 검증
                        if (!board || !Array.isArray(board) || board.length === 0) {
                            console.error("Invalid board data:", board);
                            debugElement.textContent = "Invalid board data received";
                            debugElement.className = 'error';
                            return;
                        }

                        const height = board.length;
                        const width = board[0] ? board[0].length : 0;
                        
                        console.log(`Board dimensions: ${height}x${width}`);
                        console.log(`Stones count: ${stones ? stones.length : 0}`);
                        
                        // 보드 크기가 변경되었거나, 처음 로드될 때만 보드를 새로 그립니다.
                        if (boardElement.children.length !== height * width) {
                            initializeBoard(width);
                        }

                        // 턴 정보 업데이트
                        turnInfoElement.textContent = `Turn: ${turn || 'Unknown'}`;
                        turnInfoElement.className = '';
                        
                        // 디버그 정보
                        const stoneCount = stones ? stones.length : 0;
                        debugElement.textContent = `Last update: ${new Date().toLocaleTimeString()} | Board: ${height}x${width} | Stones: ${stoneCount}`;
                        debugElement.className = '';

                        // 각 셀의 돌 상태를 업데이트합니다.
                        for (let r = 0; r < height; r++) {
                            if (!Array.isArray(board[r])) {
                                console.error(`Invalid row ${r}:`, board[r]);
                                continue;
                            }
                            
                            for (let c = 0; c < board[r].length; c++) {
                                const cellElement = document.getElementById(`cell-${r}-${c}`);
                                if (!cellElement) {
                                    console.error(`Cell not found: cell-${r}-${c}`);
                                    continue;
                                }

                                // 기존 돌을 제거합니다.
                                const existingStone = cellElement.querySelector('.stone');
                                if (existingStone) {
                                    existingStone.remove();
                                }

                                // board[r][c]의 값: null, "BLACK", "WHITE"
                                const stoneType = board[r][c];
                                
                                // null이 아니고 값이 있으면 돌을 그립니다
                                if (stoneType !== null && stoneType !== undefined) {
                                    const stoneElement = document.createElement('div');
                                    stoneElement.classList.add('stone', stoneType.toLowerCase());
                                    cellElement.appendChild(stoneElement);
                                }
                            }
                        }
                    }

                    async function fetchState() {
                        try {
                            const response = await fetch('/api/state');
                            const gameState = await response.json();
                            updateBoard(gameState);
                        } catch (e) {
                            console.error("Failed to fetch state:", e);
                            turnInfoElement.textContent = "Connection error";
                            turnInfoElement.className = 'error';
                            debugElement.textContent = "Fetch error: " + e.message;
                            debugElement.className = 'error';
                            stateJsonElement.textContent = "Error: " + e.message;
                            stateJsonElement.className = 'error';
                        }
                    }

                    // 초기 로드
                    fetchState();
                    
                    // 1초마다 상태 업데이트
                    updateInterval = setInterval(fetchState, 1000);
                    
                    // 페이지를 떠날 때 interval 정리
                    window.addEventListener('beforeunload', () => {
                        if (updateInterval) {
                            clearInterval(updateInterval);
                        }
                    });
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

    def run_server(self, host="0.0.0.0", port=8000):
        """Uvicorn 서버를 실행하는 함수"""
        uvicorn.run(self.app, host=host, port=port)
        print(f"브라우저에서 http://{host}:{port} 주소로 접속하세요.")
