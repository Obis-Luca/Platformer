"""watch_best.py - Live viewer for the best evolved platformer agent.

Opens a REAL pygame window and replays the current best evolved agent so you
can watch it play in real time. While the evolutionary trainer keeps running
and saving new bests to 'best_replay.pkl', this viewer auto-reloads and replays
the newest best each loop, letting you watch the agent improve.

Usage:
    python watch_best.py

Run this from the project root (same directory as best_replay.pkl, data.py,
Entities.py and the images/ folder). Close the window or press Ctrl+C to quit.

NOTE: This script intentionally does NOT import Model and does NOT set the
SDL_VIDEODRIVER to 'dummy', because it needs a real, visible window.
"""

import os
import sys
import time
import pickle

import pygame

from data import *
from Entities import *
import Entities

# Player.update() only draws itself when rendering is enabled.
Entities.RENDER_ENABLED = True

REPLAY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'best_replay.pkl')

# Action -> movement, replicated exactly from the trainer.
LEFT_DX = -5
RIGHT_DX = 5


def handle_quit():
    """Pump events and return True if the user asked to close the window."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
    return False


def quit_viewer():
    pygame.quit()
    sys.exit(0)


def draw_overlay(font, generation, fitness, extra=None):
    """Draw generation/fitness text (and an optional extra line) on screen."""
    lines = [
        "Generation: {}".format(generation),
        "Fitness: {:.2f}".format(fitness),
    ]
    if extra:
        lines.append(extra)
    y = 10
    for line in lines:
        surf = font.render(line, True, (255, 255, 255))
        shadow = font.render(line, True, (0, 0, 0))
        screen.blit(shadow, (12, y + 2))
        screen.blit(surf, (10, y))
        y += surf.get_height() + 4


def load_best():
    """Load best_replay.pkl as a plain dict. Returns None if unavailable."""
    try:
        with open(REPLAY_FILE, 'rb') as f:
            data = pickle.load(f)
        return data
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        # File missing or mid-write by the trainer; treat as not-ready.
        return None


def get_mtime():
    try:
        return os.path.getmtime(REPLAY_FILE)
    except OSError:
        return None


def wait_for_replay(font):
    """Block (while keeping the window responsive) until a replay exists."""
    while True:
        data = load_best()
        if data is not None:
            return data
        if handle_quit():
            quit_viewer()
        screen.blit(bg_img, (0, 0))
        display_message("Waiting for best_replay.pkl ...")
        draw_overlay(font, "-", 0.0)
        pygame.display.update()
        clock.tick(FPS)
        time.sleep(0.05)


def reset_environment():
    """Build a fresh world and player; return the new player."""
    # World.__init__ populates these module-level groups, so clear them first.
    blobGroup.empty()
    lavaGroup.empty()
    exitGroup.empty()
    checkpointGroup.empty()

    new_world = World(world_data)
    new_player = Player(100, screen_height - 130)

    # Player.update() collides against Entities.world, so point it at ours.
    Entities.world = new_world
    return new_world, new_player


def replay_run(data, font):
    """Replay one full run of the given best agent."""
    world_obj, player = reset_environment()
    genes = data.get('genes', [])
    generation = data.get('generation', '?')
    fitness = data.get('fitness', 0.0)

    game_over = 0

    for action, duration in genes:
        if game_over != 0:
            break
        for _ in range(int(duration)):
            if handle_quit():
                quit_viewer()

            dx = 0
            dy = 0
            if action == 'left':
                dx = LEFT_DX
            elif action == 'right':
                dx = RIGHT_DX
            elif action == 'jump':
                if player.onGround:
                    player.vel_y = -15
                    player.onGround = False

            # Render frame
            screen.blit(bg_img, (0, 0))
            game_over = player.update(game_over, dx, dy)

            blobGroup.update()
            blobGroup.draw(screen)
            lavaGroup.draw(screen)
            exitGroup.draw(screen)
            world_obj.draw()

            # Count/consume checkpoints exactly like the game does.
            if pygame.sprite.spritecollide(player, checkpointGroup, True):
                player.checkpointsReached += 1

            draw_overlay(font, generation, fitness)
            pygame.display.update()
            clock.tick(FPS)

            if game_over != 0:
                break

    # Briefly show the outcome of this run.
    outcome = None
    if game_over == 1:
        outcome = "Reached the EXIT!"
    elif game_over == -1:
        outcome = "Died."

    if outcome is not None:
        end = time.time() + 1.0
        while time.time() < end:
            if handle_quit():
                quit_viewer()
            screen.blit(bg_img, (0, 0))
            world_obj.draw()
            lavaGroup.draw(screen)
            exitGroup.draw(screen)
            blobGroup.draw(screen)
            screen.blit(player.image, player.rect)
            draw_overlay(font, generation, fitness, extra=outcome)
            pygame.display.update()
            clock.tick(FPS)


def main():
    pygame.font.init()
    font = pygame.font.SysFont(None, 36)

    last_mtime = None

    while True:
        if handle_quit():
            quit_viewer()

        data = wait_for_replay(font)
        last_mtime = get_mtime()

        replay_run(data, font)

        # Pause ~1.5s between runs while staying responsive, then reload the
        # newest best if the trainer has written a new one.
        end = time.time() + 1.5
        while time.time() < end:
            if handle_quit():
                quit_viewer()
            clock.tick(FPS)

        # If the file changed (or we just want the freshest), the next loop
        # iteration reloads it. Track mtime so a "watch it improve" loop picks
        # up new bests as soon as they are saved.
        current_mtime = get_mtime()
        if current_mtime is not None and current_mtime != last_mtime:
            last_mtime = current_mtime
        # Loop again: reload + replay the (possibly updated) best.


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        quit_viewer()
