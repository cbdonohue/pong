# 🏓 Pong

A clean two-player (or vs-AI) Pong game built with Python and Pygame.

## Features

- **1-player mode** — play against a simple AI
- **2-player mode** — local co-op on the same keyboard
- Score tracking — first to 7 wins
- Ball speed increases on each paddle hit
- Pause, rematch, and main menu support

## Controls

| Action | Player 1 (Left) | Player 2 (Right) |
|--------|----------------|-----------------|
| Move Up | `W` | `↑` or `I` |
| Move Down | `S` | `↓` or `K` |
| Pause | `ESC` | |

## Requirements

- Python 3.8+
- pygame

## Install & Run

```bash
pip install pygame
python pong.py
```

## Gameplay

- Ball speeds up slightly with each paddle hit
- Angle of return depends on where the ball hits the paddle
- First player to reach **7 points** wins
