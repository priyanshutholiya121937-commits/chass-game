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