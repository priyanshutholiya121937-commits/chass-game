# Chess Game (Python + Pygame)

This project is a **2-player chess game** built in Python using
**Pygame** for the graphical interface and a custom **chess logic
engine** for move validation, check/checkmate detection, castling, en
passant, and pawn promotion.

------------------------------------------------------------------------

## 🎮 Features

-   Full chess rules implementation:
    -   Legal move generation
    -   Check, checkmate, and stalemate detection
    -   Castling, en passant, and promotion support
-   Interactive **graphical chessboard** with highlights for:
    -   Selected piece
    -   Legal moves
    -   Last move
    -   Check warnings
-   Undo last move (`U` key)
-   Restart game (`R` key)
-   Unicode chess symbols for cross-platform compatibility

------------------------------------------------------------------------

## 📂 Project Structure

    .
    ├── main.py          # Pygame-based UI and game loop
    ├── chess_logic.py   # Core chess logic, move validation, and state management

------------------------------------------------------------------------


## That is full code 

# main.py

import pygame
import sys
from chess_logic import GameState

WIDTH = 720
HEIGHT = 760  # leave room for status bar
BOARD_SIZE = 720
SQ_SIZE = BOARD_SIZE // 8
FPS = 60

COLORS = {
    "light": (240, 217, 181),
    "dark": (181, 136, 99),
    "select": (187, 203, 43),
    "last_start": (246, 246, 105),
    "last_end": (246, 246, 105),
    "check": (255, 95, 95),
    "panel": (28, 28, 32),
    "panel_text": (235, 235, 235),
    "ghost": (0, 0, 0, 60),
}

# Try to find a font that includes chess glyphs ♔♕♖♗♘♙
FALLBACK_FONTS = [
    "Segoe UI Symbol",
    "DejaVu Sans",
    "Noto Sans Symbols2",
    "Arial Unicode MS",
    "Symbola",
    "FreeSerif",
]

def find_symbol_font():
    for name in FALLBACK_FONTS:
        try:
            path = pygame.font.match_font(name)
            if path:
                return path
        except Exception:
            pass
    # fallback to default
    return None

def draw_board(screen, gs, selected_sq=None, legal_moves=None, last_move=None):
    for r in range(8):
        for c in range(8):
            color = COLORS["light"] if (r + c) % 2 == 0 else COLORS["dark"]
            pygame.draw.rect(screen, color, pygame.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

    # Last move highlight
    if last_move:
        (sr, sc), (er, ec) = last_move.start, last_move.end
        pygame.draw.rect(screen, (255,255,0), pygame.Rect(sc*SQ_SIZE, sr*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
        pygame.draw.rect(screen, (255,255,0), pygame.Rect(ec*SQ_SIZE, er*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)

    # Selected square
    if selected_sq:
        r, c = selected_sq
        pygame.draw.rect(screen, COLORS["select"], pygame.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE), 6)

    # Legal moves
    if legal_moves:
        for mv in legal_moves:
            r, c = mv.end
            center = (c*SQ_SIZE + SQ_SIZE//2, r*SQ_SIZE + SQ_SIZE//2)
            pygame.draw.circle(screen, (0,0,0), center, 8)

def glyph_for_piece(piece: str) -> str:
    # piece like "wK","bQ" -> glyph
    side = piece[0]
    k = piece[1]
    if side == "w":
        return {"K":"\u2654","Q":"\u2655","R":"\u2656","B":"\u2657","N":"\u2658","P":"\u2659"}[k]
    else:
        return {"K":"\u265A","Q":"\u265B","R":"\u265C","B":"\u265D","N":"\u265E","P":"\u265F"}[k]

def draw_pieces(screen, gs, font_glyph):
    # Render chess glyphs with light drop shadow for contrast
    shadow_offset = 2
    for r in range(8):
        for c in range(8):
            p = gs.board[r][c]
            if p == ".":
                continue
            glyph = glyph_for_piece(p)
            text = font_glyph.render(glyph, True, (20,20,20))
            # outline/shadow
            screen.blit(text, text.get_rect(center=(c*SQ_SIZE + SQ_SIZE//2 + shadow_offset, r*SQ_SIZE + SQ_SIZE//2 + shadow_offset)))
            text2 = font_glyph.render(glyph, True, (250,250,250))
            screen.blit(text2, text2.get_rect(center=(c*SQ_SIZE + SQ_SIZE//2, r*SQ_SIZE + SQ_SIZE//2)))

def draw_status_bar(screen, gs, font_small):
    panel_h = HEIGHT - BOARD_SIZE
    rect = pygame.Rect(0, BOARD_SIZE, WIDTH, panel_h)
    pygame.draw.rect(screen, COLORS["panel"], rect)

    if gs.checkmate:
        msg = f"Checkmate! {'White' if not gs.white_to_move else 'Black'} wins.  R: Restart"
    elif gs.stalemate:
        msg = "Stalemate.  R: Restart"
    else:
        turn = "White" if gs.white_to_move else "Black"
        msg = f"{turn} to move.  U: Undo   R: Restart"

    label = font_small.render(msg, True, COLORS["panel_text"])
    screen.blit(label, (12, BOARD_SIZE + 10))

def draw_promotion_prompt(screen, font_glyph, side):
    # Choose from Q R B N
    glyphs_w = {"q":"\u2655","r":"\u2656","b":"\u2657","n":"\u2658"}
    glyphs_b = {"q":"\u265B","r":"\u265C","b":"\u265D","n":"\u265E"}
    glyphs = glyphs_w if side == "w" else glyphs_b

    modal_w, modal_h = 420, 160
    rect = pygame.Rect((WIDTH - modal_w)//2, (BOARD_SIZE - modal_h)//2, modal_w, modal_h)
    pygame.draw.rect(screen, (25,25,25), rect, border_radius=12)
    pygame.draw.rect(screen, (220,220,220), rect, 2, border_radius=12)
    title_font = pygame.font.SysFont(None, 28)
    title = title_font.render("Choose promotion piece", True, (240,240,240))
    screen.blit(title, (rect.x + 16, rect.y + 14))

    btns = []
    keys = ["q","r","b","n"]
    for i, k in enumerate(keys):
        bx = rect.x + 30 + i*95
        by = rect.y + 60
        brect = pygame.Rect(bx, by, 70, 70)
        pygame.draw.rect(screen, (50,50,50), brect, border_radius=10)
        pygame.draw.rect(screen, (200,200,200), brect, 1, border_radius=10)
        g = font_glyph.render(glyphs[k], True, (240,240,240))
        screen.blit(g, g.get_rect(center=brect.center))
        btns.append((brect, k))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for brect, k in btns:
                    if brect.collidepoint(mx, my):
                        return k

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess (with icons)")
    clock = pygame.time.Clock()

    # Prepare fonts
    font_path = find_symbol_font()
    if font_path:
        font_glyph = pygame.font.Font(font_path, int(SQ_SIZE*0.85))
    else:
        font_glyph = pygame.font.SysFont(None, int(SQ_SIZE*0.85))

    font_small = pygame.font.SysFont(None, 22)

    gs = GameState()
    selected_sq = None
    legal_moves_cache = []
    move_log = []

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u and move_log:
                    last = move_log.pop()
                    gs.undo_move(last)
                    selected_sq = None
                    legal_moves_cache = []
                if event.key == pygame.K_r:
                    gs = GameState()
                    selected_sq = None
                    legal_moves_cache = []
                    move_log = []

            if gs.checkmate or gs.stalemate:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = event.pos
                if y >= BOARD_SIZE:
                    continue
                r, c = y // SQ_SIZE, x // SQ_SIZE
                if gs.board[r][c] != "." and gs.board[r][c][0] == ("w" if gs.white_to_move else "b"):
                    selected_sq = (r, c)
                    legal_moves_cache = gs.get_legal_moves_from(selected_sq)
                else:
                    selected_sq = None
                    legal_moves_cache = []

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                x, y = event.pos
                if y >= BOARD_SIZE:
                    continue
                r, c = y // SQ_SIZE, x // SQ_SIZE
                if selected_sq:
                    for mv in legal_moves_cache:
                        if mv.end == (r, c):
                            if mv.promotion:
                                side = "w" if gs.white_to_move else "b"
                                mv.promotion = draw_promotion_prompt(screen, font_glyph, side)
                            gs.make_move(mv)
                            move_log.append(mv)
                            selected_sq = None
                            legal_moves_cache = []
                            break

        # Draw
        screen.fill((0,0,0))
        last_mv = move_log[-1] if move_log else None
        draw_board(screen, gs, selected_sq, legal_moves_cache, last_mv)
        draw_pieces(screen, gs, font_glyph)

        # Check highlight
        if gs.in_check(gs.white_to_move):
            kr, kc = gs.locate_king("w" if gs.white_to_move else "b")
            s = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
            s.fill((255, 0, 0, 90))
            screen.blit(s, (kc*SQ_SIZE, kr*SQ_SIZE))

        draw_status_bar(screen, gs, font_small)
        pygame.display.flip()

if __name__ == "__main__":
    main()


# chess_logic.py  

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

def algebraic_to_pos(s: str) -> Tuple[int,int]:
    file = ord(s[0].lower()) - ord('a')
    rank = 8 - int(s[1])
    return rank, file

def pos_to_algebraic(r: int, c: int) -> str:
    return chr(c + ord('a')) + str(8 - r)

@dataclass
class Move:
    start: Tuple[int,int]
    end: Tuple[int,int]
    piece: str
    captured: Optional[str] = None
    promotion: Optional[str] = None
    is_en_passant: bool = False
    is_castle: bool = False
    prev_castling: Optional[Dict[str,bool]] = None
    prev_en_passant: Optional[Tuple[int,int]] = None
    prev_halfmove: int = 0
    prev_fullmove: int = 1

class GameState:
    def __init__(self, fen: str = START_FEN):
        self.load_fen(fen)

    def load_fen(self, fen: str):
        parts = fen.split()
        board_part, turn, castling, enp, half, full = parts
        rows = board_part.split("/")
        self.board = []
        for r in rows:
            row = []
            for ch in r:
                if ch.isdigit():
                    row.extend(["."] * int(ch))
                else:
                    side = "w" if ch.isupper() else "b"
                    kind = ch.lower()
                    mapping = {"p":"P", "r":"R", "n":"N", "b":"B", "q":"Q", "k":"K"}
                    row.append(side + mapping[kind])
            self.board.append(row)
        self.white_to_move = (turn == "w")
        self.castling_rights = {
            "wK": "K" in castling,
            "wQ": "Q" in castling,
            "bK": "k" in castling,
            "bQ": "q" in castling,
        }
        self.en_passant = None if enp == "-" else algebraic_to_pos(enp)
        self.halfmove_clock = int(half)
        self.fullmove_number = int(full)
        self.checkmate = False
        self.stalemate = False

    def locate_king(self, side: str) -> Tuple[int,int]:
        target = side + "K"
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == target:
                    return (r, c)
        return (-1, -1)

    def in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def square_attacked_by(self, r, c, attacker_side) -> bool:
        pr = -1 if attacker_side == "w" else 1
        for dc in (-1, 1):
            rr, cc = r + pr, c + dc
            if self.in_bounds(rr, cc) and self.board[rr][cc] == attacker_side + "P":
                return True
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            rr, cc = r+dr, c+dc
            if self.in_bounds(rr, cc) and self.board[rr][cc] == attacker_side + "N":
                return True
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            rr, cc = r+dr, c+dc
            while self.in_bounds(rr, cc):
                p = self.board[rr][cc]
                if p != ".":
                    if p[0]==attacker_side and p[1] in ("B","Q"):
                        return True
                    break
                rr += dr; cc += dc
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            rr, cc = r+dr, c+dc
            while self.in_bounds(rr, cc):
                p = self.board[rr][cc]
                if p != ".":
                    if p[0]==attacker_side and p[1] in ("R","Q"):
                        return True
                    break
                rr += dr; cc += dc
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr==0 and dc==0: continue
                rr, cc = r+dr, c+dc
                if self.in_bounds(rr, cc) and self.board[rr][cc] == attacker_side + "K":
                    return True
        return False

    def in_check(self, white_side_turn: bool) -> bool:
        side = "w" if white_side_turn else "b"
        kr, kc = self.locate_king(side)
        return self.square_attacked_by(kr, kc, "b" if side=="w" else "w")

    def get_all_legal_moves(self) -> List['Move']:
        side = "w" if self.white_to_move else "b"
        moves = self.generate_pseudo_legal(side)
        legal = []
        for mv in moves:
            self.make_move(mv)
            if not self.in_check(not self.white_to_move):
                legal.append(mv)
            self.undo_move(mv)
        if not legal:
            if self.in_check(self.white_to_move):
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = self.stalemate = False
        return legal

    def get_legal_moves_from(self, pos: Tuple[int,int]) -> List['Move']:
        side = "w" if self.white_to_move else "b"
        pr, pc = pos
        if self.board[pr][pc] == "." or self.board[pr][pc][0] != side:
            return []
        moves = [m for m in self.generate_pseudo_legal(side) if m.start == pos]
        legal = []
        for mv in moves:
            self.make_move(mv)
            if not self.in_check(not self.white_to_move):
                legal.append(mv)
            self.undo_move(mv)
        return legal

    def generate_pseudo_legal(self, side: str) -> List['Move']:
        moves = []
        forward = -1 if side == "w" else 1
        start_rank = 6 if side == "w" else 1
        opp = "b" if side=="w" else "w"
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p == "." or p[0] != side: continue
                kind = p[1]
                if kind == "P":
                    rr = r + forward
                    if self.in_bounds(rr, c) and self.board[rr][c] == ".":
                        mv = Move((r,c),(rr,c),p)
                        if (rr == 0 and side=="w") or (rr == 7 and side=="b"):
                            mv.promotion = "q"
                        moves.append(mv)
                        if r == start_rank:
                            rr2 = r + 2*forward
                            if self.board[rr2][c] == ".":
                                moves.append(Move((r,c),(rr2,c),p))
                    for dc in (-1,1):
                        cc = c + dc
                        rr = r + forward
                        if self.in_bounds(rr, cc):
                            target = self.board[rr][cc]
                            if target != "." and target[0] == opp:
                                mv = Move((r,c),(rr,cc),p, captured=target)
                                if (rr == 0 and side=="w") or (rr == 7 and side=="b"):
                                    mv.promotion = "q"
                                moves.append(mv)
                    if self.en_passant:
                        er, ec = self.en_passant
                        if r + forward == er and abs(c - ec) == 1:
                            mv = Move((r,c),(er,ec),p, captured=opp+"P", is_en_passant=True)
                            moves.append(mv)
                elif kind == "N":
                    for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                        rr, cc = r+dr, c+dc
                        if not self.in_bounds(rr, cc): continue
                        target = self.board[rr][cc]
                        if target == "." or target[0] == opp:
                            moves.append(Move((r,c),(rr,cc),p, captured=target if target!="." else None))
                elif kind in ("B","R","Q"):
                    dirs = []
                    if kind in ("B","Q"):
                        dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
                    if kind in ("R","Q"):
                        dirs += [(-1,0),(1,0),(0,-1),(0,1)]
                    for dr, dc in dirs:
                        rr, cc = r+dr, c+dc
                        while self.in_bounds(rr, cc):
                            target = self.board[rr][cc]
                            if target == ".":
                                moves.append(Move((r,c),(rr,cc),p))
                            else:
                                if target[0] == opp:
                                    moves.append(Move((r,c),(rr,cc),p, captured=target))
                                break
                            rr += dr; cc += dc
                elif kind == "K":
                    for dr in (-1,0,1):
                        for dc in (-1,0,1):
                            if dr==0 and dc==0: continue
                            rr, cc = r+dr, c+dc
                            if not self.in_bounds(rr, cc): continue
                            target = self.board[rr][cc]
                            if target == "." or target[0]==opp:
                                moves.append(Move((r,c),(rr,cc),p, captured=target if target!="." else None))
                    if side == "w" and r==7 and c==4:
                        if self.castling_rights["wK"] and self.board[7][5]=="." and self.board[7][6]==".":
                            if not self.square_attacked_by(7,4,opp) and not self.square_attacked_by(7,5,opp) and not self.square_attacked_by(7,6,opp):
                                moves.append(Move((7,4),(7,6),p,is_castle=True))
                        if self.castling_rights["wQ"] and self.board[7][1]=="." and self.board[7][2]=="." and self.board[7][3]==".":
                            if not self.square_attacked_by(7,4,opp) and not self.square_attacked_by(7,3,opp) and not self.square_attacked_by(7,2,opp):
                                moves.append(Move((7,4),(7,2),p,is_castle=True))
                    if side == "b" and r==0 and c==4:
                        if self.castling_rights["bK"] and self.board[0][5]=="." and self.board[0][6]==".":
                            if not self.square_attacked_by(0,4,opp) and not self.square_attacked_by(0,5,opp) and not self.square_attacked_by(0,6,opp):
                                moves.append(Move((0,4),(0,6),p,is_castle=True))
                        if self.castling_rights["bQ"] and self.board[0][1]=="." and self.board[0][2]=="." and self.board[0][3]==".":
                            if not self.square_attacked_by(0,4,opp) and not self.square_attacked_by(0,3,opp) and not self.square_attacked_by(0,2,opp):
                                moves.append(Move((0,4),(0,2),p,is_castle=True))
        return moves

    def make_move(self, mv: Move):
        mv.prev_castling = self.castling_rights.copy()
        mv.prev_en_passant = self.en_passant
        mv.prev_halfmove = self.halfmove_clock
        mv.prev_fullmove = self.fullmove_number

        sr, sc = mv.start
        er, ec = mv.end
        piece = self.board[sr][sc]
        target = self.board[er][ec]

        if piece[1] == "P" or target != ".":
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if not self.white_to_move:
            self.fullmove_number += 1

        if mv.is_en_passant:
            self.board[er][ec] = piece
            self.board[sr][sc] = "."
            cap_r = er + (1 if piece[0]=="w" else -1)
            mv.captured = self.board[cap_r][ec]
            self.board[cap_r][ec] = "."
        else:
            self.board[er][ec] = piece
            self.board[sr][sc] = "."

        if mv.promotion:
            self.board[er][ec] = piece[0] + mv.promotion.upper()

        if mv.is_castle:
            if er == 7 and ec == 6:
                self.board[7][5] = "wR"; self.board[7][7] = "."
            elif er == 7 and ec == 2:
                self.board[7][3] = "wR"; self.board[7][0] = "."
            elif er == 0 and ec == 6:
                self.board[0][5] = "bR"; self.board[0][7] = "."
            elif er == 0 and ec == 2:
                self.board[0][3] = "bR"; self.board[0][0] = "."

        if piece == "wK":
            self.castling_rights["wK"] = self.castling_rights["wQ"] = False
        if piece == "bK":
            self.castling_rights["bK"] = self.castling_rights["bQ"] = False
        if piece == "wR":
            if sr == 7 and sc == 0: self.castling_rights["wQ"] = False
            if sr == 7 and sc == 7: self.castling_rights["wK"] = False
        if piece == "bR":
            if sr == 0 and sc == 0: self.castling_rights["bQ"] = False
            if sr == 0 and sc == 7: self.castling_rights["bK"] = False
        if target == "wR":
            if er == 7 and ec == 0: self.castling_rights["wQ"] = False
            if er == 7 and ec == 7: self.castling_rights["wK"] = False
        if target == "bR":
            if er == 0 and ec == 0: self.castling_rights["bQ"] = False
            if er == 0 and ec == 7: self.castling_rights["bK"] = False

        self.en_passant = None
        if piece[1] == "P" and abs(er - sr) == 2:
            ep_r = (sr + er)//2
            self.en_passant = (ep_r, ec)

        self.white_to_move = not self.white_to_move

    def undo_move(self, mv: Move):
        sr, sc = mv.start
        er, ec = mv.end

        self.white_to_move = not self.white_to_move

        if mv.is_castle:
            if er == 7 and ec == 6:
                self.board[7][7] = "wR"; self.board[7][5] = "."
            elif er == 7 and ec == 2:
                self.board[7][0] = "wR"; self.board[7][3] = "."
            elif er == 0 and ec == 6:
                self.board[0][7] = "bR"; self.board[0][5] = "."
            elif er == 0 and ec == 2:
                self.board[0][0] = "bR"; self.board[0][3] = "."

        self.board[sr][sc] = mv.piece
        if mv.is_en_passant:
            self.board[er][ec] = "."
            cap_r = er + (1 if mv.piece[0]=="w" else -1)
            self.board[cap_r][ec] = "bP" if mv.piece[0]=="w" else "wP"
        else:
            self.board[er][ec] = mv.captured if mv.captured else "."

        self.castling_rights = mv.prev_castling
        self.en_passant = mv.prev_en_passant
        self.halfmove_clock = mv.prev_halfmove
        self.fullmove_number = mv.prev_fullmove

        self.checkmate = False
        self.stalemate = False

------------------------------------------------------------------------

## 🔮 Future Improvements

-   Add **AI opponent** using Minimax/Stockfish
-   Save/load PGN games
-   Online multiplayer support
-   Better UI/animations

------------------------------------------------------------------------

## 📜 License

This project is released under the **MIT License**. Feel free to use,
modify, and distribute.
