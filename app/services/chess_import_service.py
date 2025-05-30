import asyncio
import aiohttp
import chess.pgn
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.db.models.chess import ChessGame, GamePosition
from app.db.models.user import User
from app.db.models.player_profil import PlayerProfile
from app.db.database import get_db


class ChessImportService:
    def __init__(self, db: Session):
        self.db = db
        self.chess_com_api = "https://api.chess.com/pub"
        self.lichess_api = "https://lichess.org/api"

    async def import_user_games(
        self,
        user_id: int,
        platform: str = "chess.com",
        username: str = None,
        months_back: int = 3,
    ) -> Dict:
        """
        Importe les parties d'un utilisateur depuis une plateforme
        """
        print(
            f"Début import pour user_id={user_id}, platform={platform}, username={username}"
        )

        if platform == "chess.com":
            return await self._import_chess_com_games(user_id, username, months_back)
        elif platform == "lichess":
            return await self._import_lichess_games(user_id, username, months_back)
        else:
            raise ValueError(f"Plateforme non supportée: {platform}")

    async def _import_chess_com_games(
        self, user_id: int, username: str, months_back: int
    ) -> dict:
        """Import depuis Chess.com"""
        imported = 0
        skipped = 0
        errors = []

        print(f"Import Chess.com pour {username}, {months_back} mois")

        async with aiohttp.ClientSession() as session:
            # Récupérer les parties des derniers mois
            current_date = datetime.now()

            for i in range(months_back):
                year = current_date.year
                month = current_date.month - i

                if month <= 0:
                    month += 12
                    year -= 1

                try:
                    url = f"{self.chess_com_api}/player/{username}/games/{year}/{month:02d}"
                    print(f"Requête API: {url}")

                    async with session.get(url) as response:
                        print(f"Status response: {response.status}")

                        if response.status == 200:
                            data = await response.json()
                            games = data.get("games", [])
                            print(
                                f"Nombre de parties trouvées pour {year}/{month}: {len(games)}"
                            )

                            for game_data in games:
                                try:
                                    print(
                                        f"Traitement partie: {game_data.get('uuid', 'unknown')}"
                                    )
                                    result = await self._process_chess_com_game(
                                        user_id, game_data
                                    )
                                    if result == "imported":
                                        imported += 1
                                        print(f"Partie importée avec succès")
                                    else:
                                        skipped += 1
                                        print(f"Partie ignorée: {result}")
                                except Exception as e:
                                    error_msg = f"Erreur game {game_data.get('uuid', 'unknown')}: {str(e)}"
                                    print(f"ERREUR: {error_msg}")
                                    errors.append(error_msg)
                        else:
                            error_msg = f"Erreur API Chess.com {response.status} pour {year}/{month}"
                            print(f"ERREUR: {error_msg}")
                            errors.append(error_msg)

                except Exception as e:
                    error_msg = f"Erreur mois {year}/{month}: {str(e)}"
                    print(f"ERREUR: {error_msg}")
                    errors.append(error_msg)

        print(
            f"Résultat final: {imported} importées, {skipped} ignorées, {len(errors)} erreurs"
        )
        return {"imported": imported, "skipped": skipped, "errors": errors}

    async def _process_chess_com_game(self, user_id: int, game_data: dict) -> str:
        """Traite une partie Chess.com"""
        try:
            game_id = game_data.get("uuid")
            print(f"Processing game {game_id}")

            # Vérifier si la partie existe déjà
            existing = (
                self.db.query(ChessGame)
                .filter(ChessGame.chess_com_game_id == game_id)
                .first()
            )

            if existing:
                print(f"Partie {game_id} déjà existante")
                return "skipped"

            # Récupérer les usernames
            white_username = game_data["white"]["username"]
            black_username = game_data["black"]["username"]
            print(f"White: {white_username}, Black: {black_username}")

            # Récupérer ou créer les profils de joueurs
            white_player = self._get_or_create_player_profile(
                white_username, "chess.com"
            )
            black_player = self._get_or_create_player_profile(
                black_username, "chess.com"
            )
            print(
                f"Players créés - White ID: {white_player.id}, Black ID: {black_player.id}"
            )

            # Parser le PGN pour extraire les infos
            pgn_text = game_data.get("pgn", "")
            game_info = self._parse_pgn_info(pgn_text)

            # Déterminer le résultat et le gagnant
            white_result = game_data["white"].get("result")
            black_result = game_data["black"].get("result")
            result, winner = self._determine_game_result(white_result, black_result)
            print(f"Résultat: {result}, Winner: {winner}")

            # Créer l'objet ChessGame
            chess_game = ChessGame(
                chess_com_game_id=game_id,
                chess_com_url=game_data.get("url"),
                white_player_id=white_player.id,
                black_player_id=black_player.id,
                owner_id=user_id,
                game_date=datetime.fromtimestamp(
                    game_data.get("end_time", 0), tz=timezone.utc
                ),
                time_control=game_data.get("time_control"),
                time_class=game_data.get("time_class"),
                rules=game_data.get("rules", "chess"),
                rated=game_data.get("rated", True),
                result=result,
                termination=white_result
                if white_result in ["checkmated", "resigned", "timeout", "abandoned"]
                else black_result,
                winner=winner,
                pgn=pgn_text,
                fen_final=game_info.get("fen_final"),
                total_moves=game_info.get("total_moves"),
                game_duration_seconds=game_data.get("end_time", 0)
                - game_data.get("start_time", 0),
            )

            self.db.add(chess_game)
            self.db.commit()
            print(f"Partie {game_id} sauvegardée avec succès")

            return "imported"

        except Exception as e:
            print(f"Erreur dans _process_chess_com_game: {str(e)}")
            self.db.rollback()
            raise e

    def _get_or_create_player_profile(
        self, username: str, platform: str
    ) -> PlayerProfile:
        """Récupère ou crée un profil de joueur"""
        print(f"Recherche/création player: {username} sur {platform}")

        try:
            # Chercher d'abord par le username de la plateforme

            player = (
                self.db.query(PlayerProfile)
                .filter(PlayerProfile.username == username)
                .first()
            )

            if not player:
                print(f"Création nouveau PlayerProfile pour {username}")
                # Créer un nouveau profil de joueur
                player_data = {
                    "username": username,
                    "platform": platform,
                }

                player = PlayerProfile(**player_data)
                self.db.add(player)
                self.db.flush()  # Pour obtenir l'ID
                print(f"PlayerProfile créé avec ID: {player.id}")
            else:
                print(f"PlayerProfile existant trouvé avec ID: {player.id}")

            return player

        except Exception as e:
            print(f"Erreur dans _get_or_create_player_profile: {str(e)}")
            self.db.rollback()
            raise e

    def _parse_pgn_info(self, pgn_text: str) -> dict:
        """Parse le PGN pour extraire des informations"""
        info = {}

        try:
            import io

            pgn_io = io.StringIO(pgn_text)
            game = chess.pgn.read_game(pgn_io)

            if game:
                # Compter les coups
                moves = list(game.mainline_moves())
                info["total_moves"] = len(moves)

                # Position finale
                board = game.board()
                for move in moves:
                    board.push(move)
                info["fen_final"] = board.fen()

        except Exception as e:
            print(f"Erreur parsing PGN: {e}")

        return info

    def _determine_game_result(
        self, white_result: str, black_result: str
    ) -> tuple[str, Optional[str]]:
        """Détermine le résultat de la partie et le gagnant"""
        if white_result == "win":
            return "1-0", "white"
        elif black_result == "win":
            return "0-1", "black"
        else:
            # Match nul (agreed, repetition, stalemate, timevsinsufficient, etc.)
            return "1/2-1/2", None

    async def _import_lichess_games(
        self, user_id: int, username: str, months_back: int
    ) -> dict:
        """Import depuis Lichess"""
        imported = 0
        skipped = 0
        errors = []

        print(f"Import Lichess pour {username}, {months_back} mois")

        async with aiohttp.ClientSession() as session:
            try:
                # Calculer la date de début
                since_timestamp = int(
                    (datetime.now().timestamp() - (months_back * 30 * 24 * 3600)) * 1000
                )

                url = f"{self.lichess_api}/games/user/{username}"
                params = {
                    "max": 200,
                    "rated": "true",
                    "format": "json",
                    "since": since_timestamp,
                    "moves": "true",
                    "tags": "true",
                }

                print(f"Requête Lichess: {url} avec params: {params}")

                async with session.get(url, params=params) as response:
                    print(f"Status Lichess response: {response.status}")

                    if response.status == 200:
                        games_text = await response.text()
                        lines = games_text.strip().split("\n")
                        print(f"Nombre de lignes reçues: {len(lines)}")

                        for line in lines:
                            if line.strip():
                                try:
                                    game_data = json.loads(
                                        line
                                    )  # Correction: json.loads au lieu d'eval
                                    result = await self._process_lichess_game(
                                        user_id, game_data
                                    )
                                    if result == "imported":
                                        imported += 1
                                    else:
                                        skipped += 1
                                except Exception as e:
                                    error_msg = f"Erreur game: {str(e)}"
                                    print(f"ERREUR: {error_msg}")
                                    errors.append(error_msg)
                    else:
                        error_msg = f"Erreur API Lichess {response.status}"
                        print(f"ERREUR: {error_msg}")
                        errors.append(error_msg)

            except Exception as e:
                error_msg = f"Erreur Lichess API: {str(e)}"
                print(f"ERREUR: {error_msg}")
                errors.append(error_msg)

        print(
            f"Résultat Lichess: {imported} importées, {skipped} ignorées, {len(errors)} erreurs"
        )
        return {"imported": imported, "skipped": skipped, "errors": errors}

    async def _process_lichess_game(self, user_id: int, game_data: dict) -> str:
        """Traite une partie Lichess"""
        try:
            game_id = game_data.get("id")
            print(f"Processing Lichess game {game_id}")

            # Vérifier si la partie existe déjà
            existing = (
                self.db.query(ChessGame)
                .filter(ChessGame.lichess_game_id == game_id)
                .first()
            )

            if existing:
                print(f"Partie Lichess {game_id} déjà existante")
                return "skipped"

            # Récupérer les informations des joueurs
            players = game_data.get("players", {})
            white_username = (
                players.get("white", {}).get("user", {}).get("name", "Anonymous")
            )
            black_username = (
                players.get("black", {}).get("user", {}).get("name", "Anonymous")
            )

            # Récupérer ou créer les profils de joueurs
            white_player = self._get_or_create_player_profile(white_username, "lichess")
            black_player = self._get_or_create_player_profile(black_username, "lichess")

            # Extraire les informations de la partie
            clock = game_data.get("clock", {})
            time_control = (
                f"{clock.get('initial', 0)}+{clock.get('increment', 0)}"
                if clock
                else None
            )
            time_class = self._get_lichess_time_class(
                clock.get("initial", 0) if clock else 0
            )

            # Construire le PGN
            moves = game_data.get("moves", "")
            pgn_text = self._build_lichess_pgn(game_data, moves)
            game_info = self._parse_pgn_info(pgn_text)

            # Déterminer le résultat
            winner_color = game_data.get("winner")
            if winner_color == "white":
                result = "1-0"
            elif winner_color == "black":
                result = "0-1"
            else:
                result = "1/2-1/2"

            # Créer l'objet ChessGame
            chess_game = ChessGame(
                lichess_game_id=game_id,
                lichess_url=f"https://lichess.org/{game_id}",
                white_player_id=white_player.id,
                black_player_id=black_player.id,
                owner_id=user_id,
                game_date=datetime.fromtimestamp(
                    game_data.get("createdAt", 0) / 1000, tz=timezone.utc
                ),
                time_control=time_control,
                time_class=time_class,
                rules=game_data.get("variant", "standard"),
                rated=game_data.get("rated", True),
                result=result,
                termination=game_data.get("status"),
                winner=winner_color,
                pgn=pgn_text,
                fen_final=game_info.get("fen_final"),
                total_moves=game_info.get("total_moves"),
                game_duration_seconds=(
                    game_data.get("lastMoveAt", 0) - game_data.get("createdAt", 0)
                )
                // 1000,
            )

            self.db.add(chess_game)
            self.db.commit()
            print(f"Partie Lichess {game_id} sauvegardée avec succès")

            return "imported"

        except Exception as e:
            print(f"Erreur dans _process_lichess_game: {str(e)}")
            self.db.rollback()
            raise e

    def _get_lichess_time_class(self, initial_time: int) -> str:
        """Détermine la classe de temps basée sur le temps initial (en secondes)"""
        if initial_time < 180:
            return "bullet"
        elif initial_time < 600:
            return "blitz"
        elif initial_time < 1800:
            return "rapid"
        else:
            return "classical"

    def _build_lichess_pgn(self, game_data: dict, moves: str) -> str:
        """Construit un PGN basique à partir des données Lichess"""
        players = game_data.get("players", {})
        white_name = players.get("white", {}).get("user", {}).get("name", "Anonymous")
        black_name = players.get("black", {}).get("user", {}).get("name", "Anonymous")

        date = datetime.fromtimestamp(game_data.get("createdAt", 0) / 1000)

        # En-têtes PGN
        pgn_lines = [
            f'[Event "Lichess game"]',
            f'[Site "https://lichess.org/{game_data.get("id")}"]',
            f'[Date "{date.strftime("%Y.%m.%d")}"]',
            f'[White "{white_name}"]',
            f'[Black "{black_name}"]',
            f'[Result "{self._format_lichess_result(game_data)}"]',
            f'[Variant "{game_data.get("variant", "standard")}"]',
            "",
            moves,
        ]

        return "\n".join(pgn_lines)

    def _format_lichess_result(self, game_data: dict) -> str:
        """Formate le résultat Lichess pour le PGN"""
        winner = game_data.get("winner")
        if winner == "white":
            return "1-0"
        elif winner == "black":
            return "0-1"
        else:
            return "1/2-1/2"
