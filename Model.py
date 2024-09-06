import sys
import random
from random import choice, randint, sample
import pickle
from Entities import *
from data import *

population_size = 20 # 20 for elites.pkl
chromosome_length = 200 #200 for elites.pkl
mutation_rate = 0.02
generations = 100
elite_size = 5
actions = ['left', 'right', 'jump']


class Chromosome:
    def __init__(self, gene=None):
        if gene is None:
            self.genes = [(choice(actions), randint(1, 10)) for _ in range(chromosome_length)]
        else:
            self.genes = gene
        self.fitness = 1

    def evaluate_fitness(self, render=False):
        train_player = Player(100, screen_height - 130)
        train_world = World(world_data)
        gameOver = 0

        checkpoints_reached = 0
        best_distance_to_next_checkpoint = sys.maxsize
        time_survived = 0

        for action, duration in self.genes:
            if gameOver != 0:
                break

            for _ in range(duration):
                if gameOver != 0:
                    break

                time_survived += 1

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

                # Update and draw game elements (if rendering)
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

                # Check for checkpoint collisions
                checkpoint_hits = pygame.sprite.spritecollide(train_player, checkpointGroup, True)
                if checkpoint_hits:
                    checkpoints_reached += len(checkpoint_hits)
                    best_distance_to_next_checkpoint = sys.maxsize

                # Find the closest checkpoint
                if len(checkpointGroup.sprites()) > 0:
                    # Calculate distances to all checkpoints
                    checkpoint_distances = [
                        abs(train_player.rect.x - checkpoint.rect.x) + abs(train_player.rect.y - checkpoint.rect.y)
                        for checkpoint in checkpointGroup.sprites()
                    ]
                    
                    # Find the minimum distance
                    current_distance_to_next_checkpoint = min(checkpoint_distances)
                    
                    # Update best distance if current distance is smaller
                    if current_distance_to_next_checkpoint < best_distance_to_next_checkpoint:
                        best_distance_to_next_checkpoint = current_distance_to_next_checkpoint

        self.fitness = 1000 * checkpoints_reached  

        # Adjust fitness based on distance to the closest checkpoint
        if len(checkpointGroup.sprites()) > 0:
            self.fitness += int( 5000 / (best_distance_to_next_checkpoint + 1)) # Adding 1 to avoid division by zero

        # Penalize for getting farther from the nearest checkpoint
        if len(checkpointGroup.sprites()) > 0:
            final_checkpoint_distances = [
                abs(train_player.rect.x - checkpoint.rect.x) + abs(train_player.rect.y - checkpoint.rect.y)
                for checkpoint in checkpointGroup.sprites()
            ]
            final_distance_to_next_checkpoint = min(final_checkpoint_distances)
            if final_distance_to_next_checkpoint > best_distance_to_next_checkpoint:
                self.fitness -= 10 * (final_distance_to_next_checkpoint - best_distance_to_next_checkpoint)


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


# Initialize population
# population = [Chromosome() for _ in range(population_size)]
population = load_population('elites.pkl')

# Evolution loop
for generation in range(generations):
    generation_average_fitness = 0
    print("Generation " + str(generation))

    # Evaluate fitness for each chromosome
    for chromosome in population:
        chromosome.evaluate_fitness(render=False)
        generation_average_fitness += chromosome.fitness

    # Sort population by fitness
    population.sort(key=lambda x: x.fitness, reverse=True)

    # Elitism: preserve the top N individuals
    new_population = population[:elite_size]

    # Select parents and create new offspring
    while len(new_population) < population_size:
        parents = select_parents(population)
        child1, child2 = crossover(parents[0], parents[1])
        mutate(child1)
        mutate(child2)
        new_population.append(child1)
        if len(new_population) < population_size:
            new_population.append(child2)

    population = new_population
    print(f"Generation {generation + 1} best fitness: {population[0].fitness}")
    print(f"Generation average: {generation_average_fitness // population_size}")


save_population(population, 'elites.pkl')

# Optionally render the best chromosome of the final generation
best_chromosome = population[0]
best_chromosome.evaluate_fitness(render=True)
