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