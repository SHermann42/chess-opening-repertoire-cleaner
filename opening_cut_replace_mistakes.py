#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Datei: opening_cut_replace_mistakes.py
# Zweck: Schneidet PGN-Partien am ersten Fehler einer gewählten Farbe ab und ersetzt den fehlerhaften Zug durch den besten Stockfish-Zug.
# Autor: Dr. Sven Hermann
# Lizenz: GNU GPL v3
# Copyright (C) 2026 Sven Hermann
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
Beschreibung:
Schneidet PGN-Partien am ersten Fehler einer gewählten Farbe ab
und ersetzt den fehlerhaften Zug durch den besten Stockfish-Zug.

Definition "Fehler":
    Es gibt einen alternativen legalen Zug, den Stockfish mindestens
    threshold_cp Centipawns besser bewertet als den tatsächlich gespielten Zug.

Features:
    - Analyse nur für eine gewählte Farbe (--color white|black)
    - Fehlersuche beginnt erst ab Zug X dieser Farbe (--start-move)
    - Optionales Stoppen nach max_ply Halbzügen
    - Fortschrittsanzeige mit tqdm
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

import chess
import chess.engine
import chess.pgn
from tqdm import tqdm

MATE_SCORE_CP = 100000


@dataclass
class MistakeInfo:
    ply_index: int
    played_move: chess.Move
    best_move: chess.Move
    played_score_cp: int
    best_score_cp: int
    delta_cp: int


def parse_color(color_str: str) -> chess.Color:
    color_str = color_str.strip().lower()
    if color_str in ("white", "w", "weiß", "weiss"):
        return chess.WHITE
    if color_str in ("black", "b", "schwarz"):
        return chess.BLACK
    raise ValueError("--color muss 'white' oder 'black' sein.")


def color_name_de(color: chess.Color) -> str:
    return "White" if color == chess.WHITE else "Black"


def score_to_cp(info: dict, pov: chess.Color) -> int:
    score = info["score"].pov(pov)
    cp = score.score(mate_score=MATE_SCORE_CP)
    if cp is None:
        raise ValueError("Engine lieferte keine verwertbare Bewertung.")
    return cp


def analyse_best_move(
    engine: chess.engine.SimpleEngine,
    board: chess.Board,
    limit: chess.engine.Limit,
) -> Tuple[chess.Move, int]:
    info = engine.analyse(board, limit)
    pv = info.get("pv")
    if not pv:
        raise RuntimeError("Engine lieferte keine Principal Variation (pv).")
    best_move = pv[0]
    best_score_cp = score_to_cp(info, board.turn)
    return best_move, best_score_cp


def analyse_forced_move(
    engine: chess.engine.SimpleEngine,
    board: chess.Board,
    move: chess.Move,
    limit: chess.engine.Limit,
) -> int:
    info = engine.analyse(board, limit, root_moves=[move])
    return score_to_cp(info, board.turn)


def target_start_ply(start_move: int, analyze_color: chess.Color) -> int:
    """
    start_move bezieht sich auf den Zug der analysierten Farbe.

    Beispiele:
        white, start_move=1 -> ply 0
        black, start_move=1 -> ply 1
        white, start_move=10 -> ply 18
        black, start_move=10 -> ply 19
    """
    if start_move < 1:
        raise ValueError("--start-move muss >= 1 sein.")

    if analyze_color == chess.WHITE:
        return 2 * start_move - 2
    return 2 * start_move - 1


def find_first_mistake(
    game: chess.pgn.Game,
    engine: chess.engine.SimpleEngine,
    limit: chess.engine.Limit,
    threshold_cp: int,
    analyze_color: chess.Color,
    max_ply: Optional[int] = None,
    start_move: int = 1,
) -> Optional[MistakeInfo]:
    board = game.board()
    mainline_moves = list(game.mainline_moves())
    start_ply = target_start_ply(start_move, analyze_color)

    for ply_index, move in enumerate(mainline_moves):
        if max_ply is not None and ply_index >= max_ply:
            break

        if board.turn == analyze_color and ply_index >= start_ply:
            best_move, best_score_cp = analyse_best_move(engine, board, limit)
            played_score_cp = analyse_forced_move(engine, board, move, limit)
            delta_cp = best_score_cp - played_score_cp

            if board.turn == chess.BLACK:
                best_score_cp = -best_score_cp
                played_score_cp = -played_score_cp

            if best_move != move and delta_cp >= threshold_cp:
                return MistakeInfo(
                    ply_index=ply_index,
                    played_move=move,
                    best_move=best_move,
                    played_score_cp=played_score_cp,
                    best_score_cp=best_score_cp,
                    delta_cp=delta_cp,
                )

        board.push(move)

    return None


def rebuild_game_with_replacement(
    original_game: chess.pgn.Game,
    mistake: MistakeInfo,
    annotate: bool = True,
    analyze_color: chess.Color = chess.BLACK,
) -> chess.pgn.Game:
    new_game = chess.pgn.Game()

    for key, value in original_game.headers.items():
        new_game.headers[key] = value

    new_game.headers["Result"] = "*"

    moves = list(original_game.mainline_moves())
    node = new_game

    board = original_game.board()

    for move in moves[:mistake.ply_index]:
        node = node.add_variation(move)
        board.push(move)

    played_san = board.san(mistake.played_move)
    best_san = board.san(mistake.best_move)

    node = node.add_variation(mistake.best_move)

    if annotate:
        node.comment = (
            f"{color_name_de(analyze_color)} error replaced. "
            f"played: {played_san}, "
            f"best continuation: {best_san}, "
            f"evaluation played: {mistake.played_score_cp / 100:.2f}, "
            f"best: {mistake.best_score_cp / 100:.2f}, "
            f"difference: {mistake.delta_cp / 100:.2f} pawns."
        )

    return new_game

def count_games_in_pgn(input_path: str) -> int:
    count = 0
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            count += 1
    return count


def process_pgn(
    input_path: str,
    output_path: str,
    engine_path: str,
    depth: Optional[int],
    movetime_ms: Optional[int],
    nodes: Optional[int],
    threshold_cp: int,
    max_ply: Optional[int],
    start_move: int,
    analyze_color: chess.Color,
    keep_unmodified: bool,
    annotate: bool,
    hash_mb: Optional[int],
    threads: Optional[int],
    show_progress: bool,
) -> None:
    if sum(x is not None for x in (depth, movetime_ms, nodes)) != 1:
        raise ValueError("Genau eine von --depth, --movetime-ms oder --nodes angeben.")

    if start_move < 1:
        raise ValueError("--start-move muss >= 1 sein.")

    if depth is not None:
        limit = chess.engine.Limit(depth=depth)
    elif movetime_ms is not None:
        limit = chess.engine.Limit(time=movetime_ms / 1000.0)
    else:
        limit = chess.engine.Limit(nodes=nodes)

    total_games = 0
    changed_games = 0
    failed_games = 0

    total_count = count_games_in_pgn(input_path) if show_progress else None

    engine = chess.engine.SimpleEngine.popen_uci(engine_path)

    try:
        config = {}
        if hash_mb is not None:
            config["Hash"] = hash_mb
        if threads is not None:
            config["Threads"] = threads
        if config:
            engine.configure(config)

        with open(input_path, "r", encoding="utf-8", errors="replace") as pgn_in, \
             open(output_path, "w", encoding="utf-8", newline="\n") as pgn_out:

            progress = tqdm(
                total=total_count,
                desc="Partien",
                unit="Partie",
                dynamic_ncols=True,
                disable=not show_progress,
            )

            try:
                while True:
                    game = chess.pgn.read_game(pgn_in)
                    if game is None:
                        break

                    total_games += 1

                    try:
                        mistake = find_first_mistake(
                            game=game,
                            engine=engine,
                            limit=limit,
                            threshold_cp=threshold_cp,
                            analyze_color=analyze_color,
                            max_ply=max_ply,
                            start_move=start_move,
                        )
                    except Exception as exc:
                        failed_games += 1
                        print(
                            f"[WARN] Partie {total_games}: Analyse fehlgeschlagen: {exc}",
                            file=sys.stderr,
                        )
                        if keep_unmodified:
                            print(game, file=pgn_out, end="\n\n")

                        if show_progress:
                            progress.update(1)
                            progress.set_postfix(
                                geändert=changed_games,
                                fehler=failed_games,
                            )
                        continue

                    if mistake is not None:
                        changed_games += 1
                        new_game = rebuild_game_with_replacement(
                            original_game=game,
                            mistake=mistake,
                            annotate=annotate,
                            analyze_color=analyze_color,
                        )
                        print(new_game, file=pgn_out, end="\n\n")
                    elif keep_unmodified:
                        print(game, file=pgn_out, end="\n\n")

                    if show_progress:
                        progress.update(1)
                        progress.set_postfix(
                            geändert=changed_games,
                            fehler=failed_games,
                        )
            finally:
                progress.close()

    finally:
        engine.quit()

    print(f"Partien gesamt:      {total_games}")
    print(f"Partien modifiziert: {changed_games}")
    print(f"Partien mit Fehler:  {failed_games}")
    print(f"Analysierte Farbe:   {color_name_de(analyze_color)}")
    print(f"Fehlersuche ab:      Zug {start_move} dieser Farbe")
    if keep_unmodified:
        print("Ausgabe enthält:     alle Partien")
    else:
        print("Ausgabe enthält:     nur modifizierte Partien")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Schneidet PGN-Partien am ersten Fehler einer gewählten Farbe ab "
            "und ersetzt den fehlerhaften Zug durch den besten Stockfish-Zug."
        )
    )

    parser.add_argument("--input", required=True, help="Eingabe-PGN")
    parser.add_argument("--output", required=True, help="Ausgabe-PGN")
    parser.add_argument("--engine", required=True, help="Pfad zur Stockfish-Binary")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--depth", type=int, help="Suchtiefe für Stockfish")
    group.add_argument("--movetime-ms", type=int, help="Bedenkzeit pro Analyse in Millisekunden")
    group.add_argument("--nodes", type=int, help="Maximale Knotenzahl pro Analyse")

    parser.add_argument(
        "--threshold-cp",
        type=int,
        default=40,
        help="Fehlerschwelle in Centipawns, Standard: 40 (= 0.4 Bauern)",
    )
    parser.add_argument(
        "--max-ply",
        type=int,
        default=None,
        help="Optional: nur die ersten N Halbzüge prüfen, z.B. 50 für Zug 25",
    )
    parser.add_argument(
        "--start-move",
        type=int,
        default=1,
        help="Erst ab Zug X der analysierten Farbe prüfen, Standard: 1",
    )
    parser.add_argument(
        "--color",
        type=str,
        default="black",
        help="Zu analysierende Farbe: white oder black, Standard: black",
    )
    parser.add_argument(
        "--keep-unmodified",
        action="store_true",
        help="Auch nicht modifizierte Partien in die Ausgabe schreiben",
    )
    parser.add_argument(
        "--no-annotate",
        action="store_true",
        help="Keinen Kommentar am ersetzten Zug hinzufügen",
    )
    parser.add_argument(
        "--hash-mb",
        type=int,
        default=None,
        help="Optional: Stockfish Hash in MB",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Optional: Anzahl Threads für Stockfish",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Fortschrittsanzeige deaktivieren",
    )

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        analyze_color = parse_color(args.color)

        process_pgn(
            input_path=args.input,
            output_path=args.output,
            engine_path=args.engine,
            depth=args.depth,
            movetime_ms=args.movetime_ms,
            nodes=args.nodes,
            threshold_cp=args.threshold_cp,
            max_ply=args.max_ply,
            start_move=args.start_move,
            analyze_color=analyze_color,
            keep_unmodified=args.keep_unmodified,
            annotate=not args.no_annotate,
            hash_mb=args.hash_mb,
            threads=args.threads,
            show_progress=not args.no_progress,
        )
    except Exception as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()