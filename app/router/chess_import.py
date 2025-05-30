# Endpoint FastAPI
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from typing import Annotated

from app.services.chess_import_service import ChessImportService
from app.db.models.chess import ChessGame
from app.db.database import get_db
from app.core.security import get_current_active_user

router = APIRouter(prefix="/api/chess", tags=["chess"])

db_dependency = Annotated[Session, Depends(get_db)]


class ImportRequest(BaseModel):
    platform: str  # "chess.com" ou "lichess"
    username: str
    months_back: int = 3


@router.post("/import-games")
async def import_user_games(
    request: ImportRequest,
    current_user=Depends(get_current_active_user),  # Votre système d'auth
    db: Session = Depends(get_db),
):
    """
    Importe les parties d'un utilisateur depuis Chess.com ou Lichess
    """
    try:
        import_service = ChessImportService(db)

        result = await import_service.import_user_games(
            user_id=current_user.id,
            platform=request.platform,
            username=request.username,
            months_back=request.months_back,
        )

        return {
            "message": f"Import terminé: {result['imported']} parties importées, {result['skipped']} ignorées",
            "details": result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de l'import: {str(e)}"
        )


@router.get("/games")
async def get_user_games(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    Récupère les parties de l'utilisateur depuis la base
    """
    games = (
        db.query(ChessGame)
        .filter(
            or_(
                ChessGame.white_player_id == current_user.id,
                ChessGame.black_player_id == current_user.id,
            )
        )
        .order_by(ChessGame.game_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": game.id,
            "white_player": game.white_player_username,
            "black_player": game.black_player_username,
            "result": game.result,
            "winner": game.winner,
            "game_date": game.game_date,
            "time_class": game.time_class,
            "white_rating": game.white_player_rating,
            "black_rating": game.black_player_rating,
            "platform": "chess.com" if game.chess_com_game_id else "lichess",
            "url": game.chess_com_url or game.lichess_url,
        }
        for game in games
    ]
