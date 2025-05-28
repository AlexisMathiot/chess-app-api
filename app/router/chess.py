import asyncio
import logging
import subprocess

import chess
import chess.engine
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

logging.basicConfig(level=logging.INFO)
STOCKFISH_PATH = "/home/alexis/chessEngine/stockfish/stockfish"


class PositionRequest(BaseModel):
    fen: str


@router.post("/analyze")
async def analyze_position(data: PositionRequest):
    fen = data.fen
    try:
        board = chess.Board(fen)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid FEN"})

    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            engine.configure({"Threads": 4, "Hash": 512})
            result = engine.analyse(board, chess.engine.Limit(time=1.0))
            best_move = engine.play(board, chess.engine.Limit(time=1.0)).move.uci()

            return {
                "fen": fen,
                "best_move": best_move,
                "evaluation_cp": result["score"].white().score(mate_score=10000),
                "mate_in": result["score"].white().mate(),
                "nodes": result.get("nodes"),
                "nps": result.get("nps"),
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/check-stockfish")
async def check_stockfish():
    try:
        result = subprocess.run(
            [STOCKFISH_PATH],
            input=b"uci\nquit\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2,
            check=False,
        )
        return {
            "stdout": result.stdout.decode(),
            "stderr": result.stderr.decode(),
            "returncode": result.returncode,
        }
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Stockfish test failed"})


@router.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket connected")
    engine = None

    try:
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        engine.configure({"Threads": 2, "Hash": 128})

        while True:
            fen = await websocket.receive_text()
            logging.info(f"FEN received: {fen}")

            try:
                board = chess.Board(fen)
            except ValueError:
                await websocket.send_json({"error": "Invalid FEN"})
                continue

            try:
                limit = chess.engine.Limit()
                for info in engine.analysis(board, limit):
                    if "score" in info:
                        data = {
                            "depth": info.get("depth"),
                            "nodes": info.get("nodes"),
                            "nps": info.get("nps"),
                            "score_cp": info["score"].white().score(mate_score=10000),
                            "score_mate": info["score"].white().mate(),
                            "pv": [move.uci() for move in info.get("pv", [])],
                        }
                        await websocket.send_json(data)
                        logging.info(f"Sent: {data}")

                    await asyncio.sleep(0.5)
            except Exception as analysis_err:
                logging.exception(f"Error during analysis: {analysis_err}")
                await websocket.send_json({"error": "Analysis failed"})
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
    finally:
        if engine:
            engine.quit()
            logging.info("Engine closed")
