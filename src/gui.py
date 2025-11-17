import os
import sys
import json
import asyncio
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from openai import OpenAI

from mcp_server.client import get_mcp_client
from manager import GameManager
from utils import *
from models import AVAILABLE_MODELS

# --- 설정 ---
api_key = os.environ.get("OPENROUTER_API_KEY")

mcp_client = get_mcp_client()
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

app = FastAPI()
game_manager = GameManager(mcp_client=mcp_client, openrouter_client=openrouter_client)


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 MCP 초기화"""
    await game_manager.initialize_mcp()


@app.get("/models")
async def get_models():
    """사용 가능한 모델 목록 반환"""
    return {"models": AVAILABLE_MODELS}


@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """메인 HTML 페이지"""
    # 모델 옵션을 동적으로 생성
    model_options = "\n".join(
        [
            f'<option value="{model["id"]}">{model["name"]}</option>'
            for model in AVAILABLE_MODELS
        ]
    )

    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gomoku AI Assistant</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: #f5f5f5;
                height: 100vh;
                overflow: hidden;
            }
            
            .container {
                display: flex;
                height: 100vh;
            }
            
            /* 왼쪽 채팅 영역 */
            .chat-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                background: white;
                border-right: 1px solid #e0e0e0;
            }
            
            .chat-header {
                padding: 16px 20px;
                border-bottom: 1px solid #e0e0e0;
                background: white;
            }
            
            .chat-header h1 {
                font-size: 20px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 12px;
            }
            
            .model-selector {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .model-selector label {
                font-size: 14px;
                color: #666;
            }
            
            .model-selector select {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                cursor: pointer;
            }
            
            .messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 16px;
            }
            
            .message {
                display: flex;
                gap: 12px;
                animation: fadeIn 0.3s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .message.user {
                justify-content: flex-end;
            }
            
            .message-content {
                max-width: 70%;
                padding: 12px 16px;
                border-radius: 18px;
                line-height: 1.5;
                font-size: 15px;
            }
            
            .message.user .message-content {
                background: #2f2f2f;
                color: white;
            }
            
            .message.assistant .message-content {
                background: #f0f0f0;
                color: #1a1a1a;
            }
            
            .message.system {
                justify-content: center;
            }
            
            .message.system .message-content {
                background: #e3f2fd;
                color: #1565c0;
                font-size: 13px;
                max-width: 90%;
            }
            
            .tool-call {
                margin-top: 8px;
                padding: 8px 12px;
                background: #fff3e0;
                border-radius: 8px;
                font-size: 13px;
                color: #e65100;
                font-family: 'Courier New', monospace;
            }
            
            .input-container {
                padding: 16px 20px;
                border-top: 1px solid #e0e0e0;
                background: white;
            }
            
            .input-wrapper {
                display: flex;
                gap: 10px;
                align-items: flex-end;
            }
            
            #messageInput {
                flex: 1;
                padding: 12px 16px;
                border: 1px solid #d0d0d0;
                border-radius: 20px;
                font-size: 15px;
                resize: none;
                max-height: 120px;
                font-family: inherit;
            }
            
            #messageInput:focus {
                outline: none;
                border-color: #2f2f2f;
            }
            
            #sendButton {
                padding: 10px 24px;
                background: #2f2f2f;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 15px;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            #sendButton:hover:not(:disabled) {
                background: #1a1a1a;
            }
            
            #sendButton:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            
            /* 오른쪽 바둑판 영역 */
            .board-container {
                width: 600px;
                display: flex;
                flex-direction: column;
                background: #fafafa;
                padding: 20px;
            }
            
            .board-header {
                text-align: center;
                margin-bottom: 20px;
            }
            
            .board-header h2 {
                font-size: 24px;
                color: #1a1a1a;
                margin-bottom: 10px;
            }
            
            .turn-info {
                font-size: 18px;
                color: #666;
                font-weight: 500;
            }
            
            .board-wrapper {
                flex: 1;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            #gomoku-board-container {
                padding: 20px;
                background: #e3c16f;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
            
            #gomoku-board {
                position: relative;
                width: 450px;
                height: 450px;
                background: #e3c16f;
                border: 2px solid #5a4f41;
            }
            
            .board-lines {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
            }
            
            .board-grid {
                position: absolute;
                top: 15px;
                left: 15px;
                width: 420px;
                height: 420px;
                background-image: 
                    repeating-linear-gradient(to right, transparent, transparent 30px, #5a4f41 30px, #5a4f41 31px),
                    repeating-linear-gradient(to bottom, transparent, transparent 30px, #5a4f41 30px, #5a4f41 31px);
                pointer-events: none;
            }
            
            .cell {
                position: absolute;
                width: 36px;
                height: 36px;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
                border-radius: 50%;
                transition: background-color 0.2s;
            }
            
            .cell:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            
            .cell-coordinate {
                position: absolute;
                bottom: -20px;
                left: 50%;
                transform: translateX(-50%);
                font-size: 11px;
                color: #666;
                background: rgba(255, 255, 255, 0.9);
                padding: 2px 6px;
                border-radius: 4px;
                white-space: nowrap;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s;
            }
            
            .cell:hover .cell-coordinate {
                opacity: 1;
            }
            
            .stone {
                width: 28px;
                height: 28px;
                border-radius: 50%;
                box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                position: relative;
                z-index: 10;
            }
            
            .stone.black {
                background: radial-gradient(circle at 35% 35%, #555, #000);
            }
            
            .stone.white {
                background: radial-gradient(circle at 35% 35%, #fff, #ccc);
            }
            
            .loading {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #666;
                animation: pulse 1.5s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 0.3; }
                50% { opacity: 1; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- 왼쪽: 채팅 영역 -->
            <div class="chat-container">
                <div class="chat-header">
                    <h1>🎮 Gomoku AI Assistant</h1>
                    <div class="model-selector">
                        <label>Model:</label>
                        <select id="modelSelect">
                            {model_options}
                        </select>
                    </div>
                </div>
                
                <div class="messages" id="messages">
                    <div class="message system">
                        <div class="message-content">
                            오목 게임에 대한 명령을 자연어로 입력하세요.<br>
                            예: "게임 시작해줘", "지금 보드 상태 보여줘", "7, 7에 돌을 놔줘"<br>
                            💡 바둑판을 클릭하면 좌표가 자동으로 입력됩니다!
                        </div>
                    </div>
                </div>
                
                <div class="input-container">
                    <div class="input-wrapper">
                        <textarea 
                            id="messageInput" 
                            placeholder="메시지를 입력하세요..."
                            rows="1"
                        ></textarea>
                        <button id="sendButton">전송</button>
                    </div>
                </div>
            </div>
            
            <!-- 오른쪽: 바둑판 영역 -->
            <div class="board-container">
                <div class="board-header">
                    <h2>Game Board</h2>
                    <div class="turn-info" id="turnInfo">Waiting for game...</div>
                </div>
                <div class="board-wrapper">
                    <div id="gomoku-board-container">
                        <div id="gomoku-board"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            const messagesDiv = document.getElementById('messages');
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            const modelSelect = document.getElementById('modelSelect');
            const boardElement = document.getElementById('gomoku-board');
            const turnInfoElement = document.getElementById('turnInfo');
            
            let isProcessing = false;
            
            // 바둑판 초기화
            function initializeBoard() {
                boardElement.innerHTML = '';
                
                // 격자선 추가
                const gridDiv = document.createElement('div');
                gridDiv.className = 'board-grid';
                boardElement.appendChild(gridDiv);
                
                // 교차점(셀) 생성
                const cellSize = 30; // 격자 간격
                const offset = 15; // 보드 가장자리에서 첫 교차점까지의 거리
                
                for (let r = 0; r < 15; r++) {
                    for (let c = 0; c < 15; c++) {
                        const cell = document.createElement('div');
                        cell.className = 'cell';
                        cell.id = `cell-${r}-${c}`;
                        cell.dataset.row = r;
                        cell.dataset.col = c;
                        
                        // 교차점 위치에 배치 (격자 중심에서 약간 빼서 중앙 정렬)
                        cell.style.left = (offset + c * cellSize - 12) + 'px';
                        cell.style.top = (offset + r * cellSize - 12) + 'px';
                        
                        // 좌표 표시 요소 추가
                        const coordinate = document.createElement('div');
                        coordinate.className = 'cell-coordinate';
                        coordinate.textContent = `(${c}, ${r})`;
                        cell.appendChild(coordinate);
                        
                        // 클릭 이벤트 추가
                        cell.addEventListener('click', () => {
                            const currentText = messageInput.value.trim();
                            const coordinateText = `${c}, ${r}`;
                            
                            if (currentText) {
                                messageInput.value = `${currentText} ${coordinateText}`;
                            } else {
                                messageInput.value = coordinateText;
                            }
                            
                            // 입력창에 포커스
                            messageInput.focus();
                            
                            // 높이 조정
                            messageInput.style.height = 'auto';
                            messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
                        });
                        
                        boardElement.appendChild(cell);
                    }
                }
            }
            
            // 바둑판 업데이트
            function updateBoard(gameState) {
                if (!gameState || !gameState.board) return;
                
                const { turn, board } = gameState;
                turnInfoElement.textContent = `Turn: ${turn}`;
                
                for (let r = 0; r < board.length; r++) {
                    for (let c = 0; c < board[r].length; c++) {
                        const cell = document.getElementById(`cell-${r}-${c}`);
                        if (!cell) continue;
                        
                        const existingStone = cell.querySelector('.stone');
                        if (existingStone) existingStone.remove();
                        
                        const stoneType = board[r][c];
                        if (stoneType) {
                            const stone = document.createElement('div');
                            stone.className = `stone ${stoneType.toLowerCase()}`;
                            cell.appendChild(stone);
                        }
                    }
                }
            }
            
            // 메시지 추가
            function addMessage(role, content, toolCalls = null) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role}`;
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.textContent = content;
                
                messageDiv.appendChild(contentDiv);
                
                if (toolCalls && toolCalls.length > 0) {
                    toolCalls.forEach(tool => {
                        const toolDiv = document.createElement('div');
                        toolDiv.className = 'tool-call';
                        toolDiv.textContent = `🔧 ${tool.name}(${JSON.stringify(tool.args)})`;
                        contentDiv.appendChild(toolDiv);
                    });
                }
                
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            // 로딩 메시지
            function addLoadingMessage() {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message assistant';
                messageDiv.id = 'loading-message';
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.innerHTML = '<span class="loading"></span> <span class="loading"></span> <span class="loading"></span>';
                
                messageDiv.appendChild(contentDiv);
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function removeLoadingMessage() {
                const loadingMsg = document.getElementById('loading-message');
                if (loadingMsg) loadingMsg.remove();
            }
            
            // WebSocket 메시지 처리
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'response') {
                    removeLoadingMessage();
                    
                    if (data.error) {
                        addMessage('system', `❌ Error: ${data.error}`);
                    } else {
                        addMessage('assistant', data.response, data.tool_calls);
                        if (data.state) {
                            updateBoard(data.state);
                        }
                    }
                    
                    isProcessing = false;
                    sendButton.disabled = false;
                    messageInput.disabled = false;
                }
            };
            
            ws.onopen = () => {
                console.log('✅ WebSocket 연결됨');
            };
            
            ws.onerror = (error) => {
                console.error('❌ WebSocket 오류:', error);
                addMessage('system', '연결 오류가 발생했습니다.');
            };
            
            // 메시지 전송
            function sendMessage() {
                const message = messageInput.value.trim();
                if (!message || isProcessing) return;
                
                isProcessing = true;
                sendButton.disabled = true;
                messageInput.disabled = true;
                
                addMessage('user', message);
                addLoadingMessage();
                
                ws.send(JSON.stringify({
                    message: message,
                    model: modelSelect.value
                }));
                
                messageInput.value = '';
                messageInput.style.height = 'auto';
            }
            
            // 이벤트 리스너
            sendButton.addEventListener('click', sendMessage);
            
            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            });
            
            // 초기화
            initializeBoard();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content.replace("{model_options}", model_options))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 엔드포인트"""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_message = message_data.get("message")
            model = message_data.get("model", AVAILABLE_MODELS[0]["id"])

            # 메시지 처리
            result = await game_manager.process_message(user_message, model)

            # 결과 전송
            await websocket.send_text(json.dumps({"type": "response", **result}))

    except WebSocketDisconnect:
        print("🔌 WebSocket 연결 종료")
    except Exception as e:
        print(f"❌ WebSocket 오류: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("🎮 Gomoku AI Web Application")
    print("=" * 60)
    print("서버 시작: http://127.0.0.1:8000")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
