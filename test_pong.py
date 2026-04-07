"""
Unit tests for pong.py

We import pong.py with SDL_VIDEODRIVER=dummy so pygame initialises without
a real display.  Only module-level code runs on import (constants + function
definitions); main() is never called, so no window opens.
"""

import os
import sys
import math
import unittest

# Tell SDL/pygame not to open a real window
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Make sure the test can find pong.py when run from any directory
sys.path.insert(0, os.path.dirname(__file__))

import pong  # noqa: E402 – must come after env vars are set


# ─────────────────────────────────────────────────────────────────────────────
# Helpers / constants pulled from the module
# ─────────────────────────────────────────────────────────────────────────────
WIDTH          = pong.WIDTH
HEIGHT         = pong.HEIGHT
PADDLE_W       = pong.PADDLE_W
PADDLE_H       = pong.PADDLE_H
BALL_SIZE      = pong.BALL_SIZE
BALL_SPEED_INIT = pong.BALL_SPEED_INIT
BALL_SPEED_MAX  = pong.BALL_SPEED_MAX
BALL_SPEED_INC  = pong.BALL_SPEED_INC
PADDLE_SPEED   = pong.PADDLE_SPEED
WIN_SCORE      = 7


# ─────────────────────────────────────────────────────────────────────────────
# 1. clamp
# ─────────────────────────────────────────────────────────────────────────────
class TestClamp(unittest.TestCase):

    def test_below_lo_returns_lo(self):
        self.assertEqual(pong.clamp(-5, 0, 10), 0)

    def test_above_hi_returns_hi(self):
        self.assertEqual(pong.clamp(15, 0, 10), 10)

    def test_within_range_unchanged(self):
        self.assertEqual(pong.clamp(5, 0, 10), 5)

    def test_exactly_lo(self):
        self.assertEqual(pong.clamp(0, 0, 10), 0)

    def test_exactly_hi(self):
        self.assertEqual(pong.clamp(10, 0, 10), 10)

    def test_floats(self):
        self.assertAlmostEqual(pong.clamp(0.5, 0.0, 1.0), 0.5)
        self.assertAlmostEqual(pong.clamp(-0.1, 0.0, 1.0), 0.0)
        self.assertAlmostEqual(pong.clamp(1.1, 0.0, 1.0), 1.0)

    def test_equal_lo_hi(self):
        self.assertEqual(pong.clamp(42, 7, 7), 7)


# ─────────────────────────────────────────────────────────────────────────────
# 2. reset_ball
# ─────────────────────────────────────────────────────────────────────────────
class TestResetBall(unittest.TestCase):

    def _assert_valid(self, ball):
        self.assertIn("x",  ball)
        self.assertIn("y",  ball)
        self.assertIn("vx", ball)
        self.assertIn("vy", ball)

    def test_returns_dict_with_required_keys(self):
        b = pong.reset_ball()
        self._assert_valid(b)

    def test_spawns_at_center(self):
        b = pong.reset_ball()
        self.assertEqual(b["x"], WIDTH  // 2)
        self.assertEqual(b["y"], HEIGHT // 2)

    def test_initial_speed_correct(self):
        for _ in range(20):
            b = pong.reset_ball()
            speed = math.hypot(b["vx"], b["vy"])
            # speed should be close to BALL_SPEED_INIT (vy = tan(angle)*speed
            # and vx = dx*speed, so |vx| == BALL_SPEED_INIT exactly)
            self.assertAlmostEqual(abs(b["vx"]), BALL_SPEED_INIT)

    def test_forced_dx_positive(self):
        b = pong.reset_ball(dx=1)
        self.assertGreater(b["vx"], 0)

    def test_forced_dx_negative(self):
        b = pong.reset_ball(dx=-1)
        self.assertLess(b["vx"], 0)

    def test_random_dx_is_either_direction(self):
        directions = set()
        for _ in range(100):
            b = pong.reset_ball()
            directions.add(1 if b["vx"] > 0 else -1)
        self.assertEqual(directions, {-1, 1},
                         "reset_ball should sometimes go left and sometimes right")

    def test_vy_within_expected_range(self):
        """vy = tan(angle) * BALL_SPEED_INIT, angle in (-0.6, 0.6)"""
        max_vy = math.tan(0.6) * BALL_SPEED_INIT
        for _ in range(50):
            b = pong.reset_ball()
            self.assertLessEqual(abs(b["vy"]), max_vy + 1e-9)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Wall bounce logic
# We replicate the exact bounce checks from main() as pure functions so we
# can test them without a running game loop.
# ─────────────────────────────────────────────────────────────────────────────
def apply_wall_bounce(ball):
    """Mirror of the top/bottom bounce code in main()."""
    if ball["y"] - BALL_SIZE // 2 <= 0:
        ball["y"] = BALL_SIZE // 2
        ball["vy"] = abs(ball["vy"])
    if ball["y"] + BALL_SIZE // 2 >= HEIGHT:
        ball["y"] = HEIGHT - BALL_SIZE // 2
        ball["vy"] = -abs(ball["vy"])
    return ball


class TestWallBounce(unittest.TestCase):

    def _make_ball(self, x, y, vx, vy):
        return {"x": x, "y": y, "vx": vx, "vy": vy}

    def test_top_wall_reverses_vy(self):
        b = self._make_ball(WIDTH // 2, 0, 3, -4)  # moving up, at top edge
        b = apply_wall_bounce(b)
        self.assertGreater(b["vy"], 0, "vy should be positive after top bounce")

    def test_top_wall_clamps_y(self):
        b = self._make_ball(WIDTH // 2, 0, 3, -4)
        b = apply_wall_bounce(b)
        self.assertEqual(b["y"], BALL_SIZE // 2)

    def test_bottom_wall_reverses_vy(self):
        b = self._make_ball(WIDTH // 2, HEIGHT, 3, 4)
        b = apply_wall_bounce(b)
        self.assertLess(b["vy"], 0, "vy should be negative after bottom bounce")

    def test_bottom_wall_clamps_y(self):
        b = self._make_ball(WIDTH // 2, HEIGHT, 3, 4)
        b = apply_wall_bounce(b)
        self.assertEqual(b["y"], HEIGHT - BALL_SIZE // 2)

    def test_no_bounce_in_middle(self):
        b = self._make_ball(WIDTH // 2, HEIGHT // 2, 3, -2)
        b = apply_wall_bounce(b)
        self.assertEqual(b["vy"], -2, "vy should not change mid-field")

    def test_top_bounce_already_moving_down_unchanged(self):
        """Ball at top but vy already positive – abs() keeps it positive."""
        b = self._make_ball(WIDTH // 2, 0, 3, 2)
        b = apply_wall_bounce(b)
        self.assertGreater(b["vy"], 0)

    def test_bottom_bounce_already_moving_up_unchanged(self):
        b = self._make_ball(WIDTH // 2, HEIGHT, 3, -2)
        b = apply_wall_bounce(b)
        self.assertLess(b["vy"], 0)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Paddle collision – angle and speed math
# ─────────────────────────────────────────────────────────────────────────────
def apply_paddle_hit(ball, paddle_y, side):
    """
    Mirror of the paddle-collision block in main().
    paddle_y  – top of the paddle rect
    side      – "left" or "right"
    Returns updated ball dict.
    """
    rel   = (ball["y"] - (paddle_y + PADDLE_H // 2)) / (PADDLE_H // 2)
    angle = rel * 0.9
    speed = min(abs(ball["vx"]) + BALL_SPEED_INC, BALL_SPEED_MAX)
    if side == "left":
        ball["vx"] = abs(speed)
    else:
        ball["vx"] = -abs(speed)
    ball["vy"] = math.sin(angle) * speed
    return ball


class TestPaddleCollision(unittest.TestCase):

    def _make_ball(self, y, vx=-5, vy=0):
        return {"x": WIDTH // 4, "y": y, "vx": vx, "vy": vy}

    # ── Direction ────────────────────────────────────────────────────────────

    def test_left_paddle_deflects_right(self):
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        b = apply_paddle_hit(self._make_ball(HEIGHT // 2), paddle_y, "left")
        self.assertGreater(b["vx"], 0)

    def test_right_paddle_deflects_left(self):
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        b = apply_paddle_hit(self._make_ball(HEIGHT // 2, vx=5), paddle_y, "right")
        self.assertLess(b["vx"], 0)

    # ── Center hit → nearly flat ─────────────────────────────────────────────

    def test_center_hit_vy_near_zero(self):
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        ball_y   = HEIGHT // 2          # exactly paddle center
        b = apply_paddle_hit(self._make_ball(ball_y), paddle_y, "left")
        self.assertAlmostEqual(b["vy"], 0.0, places=5)

    # ── Top hit → negative vy (upward) ──────────────────────────────────────

    def test_top_hit_vy_negative(self):
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        ball_y   = paddle_y             # top edge of paddle
        b = apply_paddle_hit(self._make_ball(ball_y), paddle_y, "left")
        self.assertLess(b["vy"], 0)

    # ── Bottom hit → positive vy (downward) ─────────────────────────────────

    def test_bottom_hit_vy_positive(self):
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        ball_y   = paddle_y + PADDLE_H  # bottom edge of paddle
        b = apply_paddle_hit(self._make_ball(ball_y), paddle_y, "left")
        self.assertGreater(b["vy"], 0)

    # ── Speed increase ───────────────────────────────────────────────────────

    def test_speed_increases_after_hit(self):
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        initial_vx = 5.0
        b = apply_paddle_hit(self._make_ball(HEIGHT // 2, vx=initial_vx), paddle_y, "left")
        self.assertGreater(abs(b["vx"]), initial_vx)

    def test_speed_capped_at_max(self):
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        # Start already at max speed
        b = apply_paddle_hit(self._make_ball(HEIGHT // 2, vx=BALL_SPEED_MAX), paddle_y, "left")
        self.assertLessEqual(abs(b["vx"]), BALL_SPEED_MAX)

    def test_speed_increment_correct(self):
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        initial_speed = 5.0
        b = apply_paddle_hit(self._make_ball(HEIGHT // 2, vx=initial_speed), paddle_y, "left")
        expected = min(initial_speed + BALL_SPEED_INC, BALL_SPEED_MAX)
        self.assertAlmostEqual(abs(b["vx"]), expected)

    # ── Angle magnitude ──────────────────────────────────────────────────────

    def test_angle_bounded(self):
        """Max rel=1 → angle=0.9 rad → sin(0.9)≈0.784"""
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        max_sin  = math.sin(0.9)
        for rel_frac in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            ball_y = (paddle_y + PADDLE_H // 2) + rel_frac * (PADDLE_H // 2)
            b = apply_paddle_hit(self._make_ball(ball_y), paddle_y, "left")
            speed = abs(b["vx"])
            self.assertLessEqual(abs(b["vy"]), max_sin * BALL_SPEED_MAX + 1e-9)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Win condition
# ─────────────────────────────────────────────────────────────────────────────
def check_winner(score):
    """Return winning player index (0 or 1) or None."""
    for i in range(2):
        if score[i] >= WIN_SCORE:
            return i
    return None


class TestWinCondition(unittest.TestCase):

    def test_no_winner_at_start(self):
        self.assertIsNone(check_winner([0, 0]))

    def test_no_winner_just_below(self):
        self.assertIsNone(check_winner([WIN_SCORE - 1, WIN_SCORE - 1]))

    def test_left_wins(self):
        self.assertEqual(check_winner([WIN_SCORE, 3]), 0)

    def test_right_wins(self):
        self.assertEqual(check_winner([3, WIN_SCORE]), 1)

    def test_win_at_exact_score(self):
        self.assertEqual(check_winner([WIN_SCORE, 0]), 0)
        self.assertEqual(check_winner([0, WIN_SCORE]), 1)

    def test_win_above_score(self):
        # shouldn't happen in game, but logic should still work
        self.assertEqual(check_winner([WIN_SCORE + 2, 0]), 0)

    def test_left_checked_first(self):
        # If both somehow reach WIN_SCORE, left (index 0) is checked first
        self.assertEqual(check_winner([WIN_SCORE, WIN_SCORE]), 0)


# ─────────────────────────────────────────────────────────────────────────────
# 6. AI paddle direction
# ─────────────────────────────────────────────────────────────────────────────
def ai_move(paddle_y, ball_y):
    """
    Mirror of the AI logic in main().
    Returns the delta to apply to paddle_y this frame.
    """
    center = paddle_y + PADDLE_H // 2
    diff   = ball_y - center
    ai_spd = min(PADDLE_SPEED - 1, abs(diff))
    return ai_spd * (1 if diff > 0 else -1)


class TestAIDirection(unittest.TestCase):

    def _paddle_center_y(self):
        return HEIGHT // 2 - PADDLE_H // 2

    def test_ai_moves_up_when_ball_above(self):
        paddle_y = self._paddle_center_y()
        center   = paddle_y + PADDLE_H // 2
        ball_y   = center - 50          # ball above paddle centre
        delta = ai_move(paddle_y, ball_y)
        self.assertLess(delta, 0, "AI should move paddle up when ball is above")

    def test_ai_moves_down_when_ball_below(self):
        paddle_y = self._paddle_center_y()
        center   = paddle_y + PADDLE_H // 2
        ball_y   = center + 50          # ball below paddle centre
        delta = ai_move(paddle_y, ball_y)
        self.assertGreater(delta, 0, "AI should move paddle down when ball is below")

    def test_ai_speed_capped_at_paddle_speed_minus_one(self):
        paddle_y = 0
        ball_y   = HEIGHT              # large offset
        delta = ai_move(paddle_y, ball_y)
        self.assertLessEqual(abs(delta), PADDLE_SPEED - 1)

    def test_ai_speed_proportional_for_small_offset(self):
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        center   = paddle_y + PADDLE_H // 2
        small_diff = 2
        ball_y   = center + small_diff
        delta = ai_move(paddle_y, ball_y)
        self.assertEqual(delta, small_diff)

    def test_ai_stationary_when_aligned(self):
        paddle_y = HEIGHT // 2 - PADDLE_H // 2
        center   = paddle_y + PADDLE_H // 2
        delta = ai_move(paddle_y, center)
        self.assertEqual(delta, 0)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    unittest.main()
