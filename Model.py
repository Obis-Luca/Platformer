import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import sys
import random
import pickle
import argparse
from random import choice, randint, sample

import Entities
from Entities import *
from data import *

population_size = 20  # 20 for elites.pkl
chromosome_length = 200  # 200 for elites.pkl
mutation_rate = 0.02
elite_size = 5
actions = ['left', 'right', 'jump']

# Fitness tuning constants
PROGRESS_WEIGHT = 10
CHECKPOINT_REWARD = 500
SOLVE_BONUS = 50000
DEATH_PENALTY = 2000
TIME_BONUS_SCALE = 20


class Chromosome:
    def __init__(self, gene=None):
        if gene is None:
            self.genes = [(choice(actions), randint(1, 10)) for _ in range(chromosome_length)]
        else:
            self.genes = gene
        self.fitness = 1
        self.max_progress = 0
        self.checkpoints = 0
        self.solved = False

    def evaluate_fitness(self, render=False):
        Entities.RENDER_ENABLED = render

        train_player = Player(100, screen_height - 130)
        train_world = World(world_data)
        gameOver = 0

        # Capture exit rect once and compute its center.
        exit_rect = exitGroup.sprites()[0].rect
        exit_cx = exit_rect.centerx
        exit_cy = exit_rect.centery

        checkpoints_reached = 0
        steps = 0
        min_dist_to_exit = sys.maxsize
        start_dist = None
        solved = False
        died = False

        # Maximum number of frames this genome could run.
        max_possible_steps = sum(duration for _, duration in self.genes)

        for action, duration in self.genes:
            if gameOver != 0:
                break

            for _ in range(duration):
                if gameOver != 0:
                    break

                steps += 1

                dx, dy = 0, 0
                if action == 'left':
                    dx = -5
                elif action == 'right':
                    dx = 5
                elif action == 'jump' and train_player.onGround:
                    train_player.vel_y = -15
                    train_player.onGround = False

                if render:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            return

                    screen.blit(bg_img, (0, 0))

                gameOver = train_player.update(gameOver, dx, dy)

                blobGroup.update()
                lavaGroup.update()
                exitGroup.update()
                checkpointGroup.update()

                if render:
                    blobGroup.draw(screen)
                    lavaGroup.draw(screen)
                    exitGroup.draw(screen)
                    train_world.draw()
                    pygame.display.update()
                    clock.tick(FPS)

                # Manhattan distance to the exit.
                dist = abs(train_player.rect.centerx - exit_cx) + abs(train_player.rect.centery - exit_cy)
                if start_dist is None:
                    start_dist = dist
                if dist < min_dist_to_exit:
                    min_dist_to_exit = dist

                # Check for checkpoint collisions.
                checkpoint_hits = pygame.sprite.spritecollide(train_player, checkpointGroup, True)
                if checkpoint_hits:
                    checkpoints_reached += len(checkpoint_hits)

                if gameOver == 1:
                    solved = True
                    break
                if gameOver == -1:
                    died = True
                    break

        if start_dist is None:
            start_dist = 0

        progress = max(0, start_dist - min_dist_to_exit)
        self.fitness = progress * PROGRESS_WEIGHT + checkpoints_reached * CHECKPOINT_REWARD
        if solved:
            self.fitness += SOLVE_BONUS + TIME_BONUS_SCALE * max(0, max_possible_steps - steps)
        if died:
            self.fitness -= DEATH_PENALTY

        # Store for logging.
        self.max_progress = progress
        self.checkpoints = checkpoints_reached
        self.solved = solved

        blobGroup.empty()
        lavaGroup.empty()
        exitGroup.empty()
        checkpointGroup.empty()


def select_parents(population, tournament_size=5):
    selected = []
    for _ in range(2):
        tournament = sample(population, tournament_size)
        tournament.sort(key=lambda x: x.fitness, reverse=True)
        selected.append(tournament[0])
    return selected


def crossover(parent1: Chromosome, parent2: Chromosome):
    crossover_point1 = randint(0, chromosome_length - 1)
    crossover_point2 = randint(crossover_point1, chromosome_length - 1)
    child1_genes = parent1.genes[:crossover_point1] + parent2.genes[crossover_point1:crossover_point2] + parent1.genes[
                                                                                                         crossover_point2:]
    child2_genes = parent2.genes[:crossover_point1] + parent1.genes[crossover_point1:crossover_point2] + parent2.genes[
                                                                                                         crossover_point2:]
    return Chromosome(child1_genes), Chromosome(child2_genes)


def mutate(mutated_chromosome: Chromosome):
    for i in range(chromosome_length):
        if random.random() < mutation_rate:
            mutated_chromosome.genes[i] = (choice(actions), randint(1, 10))


def save_population(population, filename):
    with open(filename, 'wb') as file:
        pickle.dump(population, file)


def load_population(filename):
    with open(filename, 'rb') as file:
        return pickle.load(file)


def train(generations=100, resume=False, seed=42):
    random.seed(seed)

    # Initialize population.
    if resume and os.path.exists('elites.pkl'):
        population = load_population('elites.pkl')
    else:
        population = [Chromosome() for _ in range(population_size)]

    # Set up CSV logging.
    log_path = 'training_log.csv'
    write_header = not os.path.exists(log_path)
    log_file = open(log_path, 'a')
    if write_header:
        log_file.write('generation,best_fitness,avg_fitness,best_progress,best_checkpoints,solved\n')
        log_file.flush()

    try:
        for generation in range(generations):
            total_fitness = 0

            # Evaluate fitness for each chromosome.
            for chromosome in population:
                chromosome.evaluate_fitness(render=False)
                total_fitness += chromosome.fitness

            avg_fitness = total_fitness / population_size

            # Sort population by fitness (descending).
            population.sort(key=lambda x: x.fitness, reverse=True)
            best = population[0]

            # CSV log row for this generation.
            log_file.write(
                f"{generation},{best.fitness},{avg_fitness},{best.max_progress},"
                f"{best.checkpoints},{1 if best.solved else 0}\n"
            )
            log_file.flush()

            # Save the best individual's replay as a plain dict.
            replay = {'genes': list(best.genes), 'generation': generation, 'fitness': best.fitness}
            with open('best_replay.pkl', 'wb') as rf:
                pickle.dump(replay, rf)

            # Concise per-generation report.
            solved_str = " SOLVED!" if best.solved else ""
            print(
                f"Gen {generation}: best={best.fitness} avg={avg_fitness:.1f} "
                f"checkpoints={best.checkpoints}{solved_str}"
            )

            # Elitism: preserve the top N individuals.
            new_population = population[:elite_size]

            # Select parents and create new offspring.
            while len(new_population) < population_size:
                parents = select_parents(population)
                child1, child2 = crossover(parents[0], parents[1])
                mutate(child1)
                mutate(child2)
                new_population.append(child1)
                if len(new_population) < population_size:
                    new_population.append(child2)

            population = new_population
    finally:
        log_file.close()

    save_population(population, 'elites.pkl')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train the evolutionary platformer agent.')
    parser.add_argument('--generations', type=int, default=100)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    train(generations=args.generations, resume=args.resume, seed=args.seed)
