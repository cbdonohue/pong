import pygame
import sys
import random

# ── Constants ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 800, 600
FPS = 60

PADDLE_W, PADDLE_H = 12, 80
BALL_SIZE = 14
PADDLE_SPEED = 6
BALL_SPEED_INIT = 5
BALL_SPEED_MAX = 12
BALL_SPEED_INC = 0.3

WHITE  = (255, 255, 255)
BLACK  = (  0,   0,   0)
GRAY   = (180, 180, 180)
CYAN   = ( 80, 220, 220)
ORANGE = (255, 160,  30)

# ── Helpers ──────────────────────────────────────────────────────────────────
def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def reset_ball(dx=None):
    speed = BALL_SPEED_INIT
    if dx is None:
        dx = random.choice([-1, 1])
    angle = random.uniform(-0.6, 0.6)          # radians, modest vertical tilt
    import math
    return {
        "x": WIDTH // 2,
        "y": HEIGHT // 2,
        "vx": dx * speed,
        "vy": math.tan(angle) * speed,
    }

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pong")
    clock = pygame.time.Clock()
    font_large = pygame.font.SysFont("monospace", 72, bold=True)
    font_small  = pygame.font.SysFont("monospace", 24)
    font_tiny   = pygame.font.SysFont("monospace", 18)

    # Paddles: left (player 1) / right (player 2 or AI)
    left_paddle  = pygame.Rect(20,            HEIGHT//2 - PADDLE_H//2, PADDLE_W, PADDLE_H)
    right_paddle = pygame.Rect(WIDTH-20-PADDLE_W, HEIGHT//2 - PADDLE_H//2, PADDLE_W, PADDLE_H)

    ball = reset_ball()
    score = [0, 0]
    WIN_SCORE = 7

    # Game states: "menu", "playing", "paused", "gameover"
    state = "menu"
    two_player = False
    winner = None

    def draw_dashed_center():
        for y in range(0, HEIGHT, 20):
            pygame.draw.rect(screen, GRAY, (WIDTH//2 - 1, y, 2, 10))

    def draw_scores():
        left_txt  = font_large.render(str(score[0]), True, CYAN)
        right_txt = font_large.render(str(score[1]), True, ORANGE)
        screen.blit(left_txt,  (WIDTH//4  - left_txt.get_width()//2,  20))
        screen.blit(right_txt, (3*WIDTH//4 - right_txt.get_width()//2, 20))

    def draw_paddles():
        pygame.draw.rect(screen, CYAN,   left_paddle,  border_radius=4)
        pygame.draw.rect(screen, ORANGE, right_paddle, border_radius=4)

    def draw_ball(b):
        pygame.draw.ellipse(screen, WHITE,
                            (int(b["x"]) - BALL_SIZE//2,
                             int(b["y"]) - BALL_SIZE//2,
                             BALL_SIZE, BALL_SIZE))

    while True:
        clock.tick(FPS)
        screen.fill(BLACK)

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if state == "menu":
                    if event.key == pygame.K_1:
                        two_player = False; state = "playing"
                        score = [0, 0]; ball = reset_ball()
                    elif event.key == pygame.K_2:
                        two_player = True;  state = "playing"
                        score = [0, 0]; ball = reset_ball()

                elif state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        state = "paused"

                elif state == "paused":
                    if event.key == pygame.K_ESCAPE:
                        state = "playing"
                    elif event.key == pygame.K_q:
                        state = "menu"

                elif state == "gameover":
                    if event.key == pygame.K_r:
                        score = [0, 0]; ball = reset_ball(); state = "playing"
                    elif event.key == pygame.K_q:
                        state = "menu"

        # ── Menu ─────────────────────────────────────────────────────────────
        if state == "menu":
            title = font_large.render("PONG", True, WHITE)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 140))
            for i, line in enumerate([
                "Press  1  — 1 Player (vs AI)",
                "Press  2  — 2 Players",
                "",
                "Controls:",
                "Left paddle :  W / S",
                "Right paddle:  ↑ / ↓  (or I / K in 2P)",
            ]):
                t = font_small.render(line, True, GRAY)
                screen.blit(t, (WIDTH//2 - t.get_width()//2, 280 + i * 34))
            pygame.display.flip()
            continue

        # ── Game Over ────────────────────────────────────────────────────────
        if state == "gameover":
            draw_dashed_center(); draw_scores(); draw_paddles()
            color = CYAN if winner == 0 else ORANGE
            label = "LEFT WINS!" if winner == 0 else "RIGHT WINS!"
            t = font_large.render(label, True, color)
            screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 60))
            for i, line in enumerate(["R — Rematch", "Q — Main Menu"]):
                s2 = font_small.render(line, True, GRAY)
                screen.blit(s2, (WIDTH//2 - s2.get_width()//2, HEIGHT//2 + 40 + i * 34))
            pygame.display.flip()
            continue

        # ── Paused ───────────────────────────────────────────────────────────
        if state == "paused":
            draw_dashed_center(); draw_scores(); draw_paddles(); draw_ball(ball)
            t = font_large.render("PAUSED", True, WHITE)
            screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 40))
            for i, line in enumerate(["ESC — Resume", "Q — Quit to Menu"]):
                s2 = font_small.render(line, True, GRAY)
                screen.blit(s2, (WIDTH//2 - s2.get_width()//2, HEIGHT//2 + 50 + i * 34))
            pygame.display.flip()
            continue

        # ── Playing ──────────────────────────────────────────────────────────
        keys = pygame.key.get_pressed()

        # Left paddle (W/S)
        if keys[pygame.K_w]: left_paddle.y -= PADDLE_SPEED
        if keys[pygame.K_s]: left_paddle.y += PADDLE_SPEED
        left_paddle.y = clamp(left_paddle.y, 0, HEIGHT - PADDLE_H)

        # Right paddle — human (↑/↓ or I/K) or AI
        if two_player:
            if keys[pygame.K_UP]   or keys[pygame.K_i]: right_paddle.y -= PADDLE_SPEED
            if keys[pygame.K_DOWN] or keys[pygame.K_k]: right_paddle.y += PADDLE_SPEED
        else:
            # Simple AI: track ball with limited speed
            center = right_paddle.y + PADDLE_H // 2
            diff   = ball["y"] - center
            ai_spd = min(PADDLE_SPEED - 1, abs(diff))
            right_paddle.y += ai_spd * (1 if diff > 0 else -1)
        right_paddle.y = clamp(right_paddle.y, 0, HEIGHT - PADDLE_H)

        # Move ball
        ball["x"] += ball["vx"]
        ball["y"] += ball["vy"]

        # Top / bottom wall bounce
        if ball["y"] - BALL_SIZE//2 <= 0:
            ball["y"] = BALL_SIZE//2
            ball["vy"] = abs(ball["vy"])
        if ball["y"] + BALL_SIZE//2 >= HEIGHT:
            ball["y"] = HEIGHT - BALL_SIZE//2
            ball["vy"] = -abs(ball["vy"])

        # Paddle collisions
        ball_rect = pygame.Rect(int(ball["x"]) - BALL_SIZE//2,
                                int(ball["y"]) - BALL_SIZE//2,
                                BALL_SIZE, BALL_SIZE)

        for paddle, side in [(left_paddle, "left"), (right_paddle, "right")]:
            if ball_rect.colliderect(paddle):
                # Relative hit position (-1 top … +1 bottom)
                rel = (ball["y"] - (paddle.y + PADDLE_H//2)) / (PADDLE_H//2)
                import math
                angle = rel * 0.9   # max ~52°
                speed = min(abs(ball["vx"]) + BALL_SPEED_INC, BALL_SPEED_MAX)
                if side == "left":
                    ball["vx"] =  abs(speed)
                    ball["x"]  = left_paddle.right + BALL_SIZE//2 + 1
                else:
                    ball["vx"] = -abs(speed)
                    ball["x"]  = right_paddle.left - BALL_SIZE//2 - 1
                ball["vy"] = math.sin(angle) * speed

        # Scoring
        if ball["x"] < 0:
            score[1] += 1
            ball = reset_ball(dx=1)
            left_paddle.y = right_paddle.y = HEIGHT//2 - PADDLE_H//2
        elif ball["x"] > WIDTH:
            score[0] += 1
            ball = reset_ball(dx=-1)
            left_paddle.y = right_paddle.y = HEIGHT//2 - PADDLE_H//2

        # Win check
        for i in range(2):
            if score[i] >= WIN_SCORE:
                winner = i; state = "gameover"

        # ── Draw ─────────────────────────────────────────────────────────────
        draw_dashed_center()
        draw_scores()
        draw_paddles()
        draw_ball(ball)

        hint = font_tiny.render("ESC = pause", True, (60, 60, 60))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 24))

        pygame.display.flip()


if __name__ == "__main__":
    main()
