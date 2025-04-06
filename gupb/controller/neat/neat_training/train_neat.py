import neat
import random as classic_random
from gupb import runner
from gupb.controller import random
from gupb.controller.neat.kim_dzong_neat_jr import KimDzongNeatJuniorController
from gupb.controller.neat.neat_training.neat_evaluator import NeatEvaluatorV1, NeatEvaluator, NeatEvaluatorVT1
from gupb.model import games


def default_game_configuration(controller: KimDzongNeatJuniorController):
    return {
        'arenas': [
            'ordinary_chaos'
        ],
        'controllers': [
            controller,
            random.RandomController("Alice"),
            random.RandomController("Bob"),
            random.RandomController("Cecilia"),
            random.RandomController("Darius"),
        ],
        'start_balancing': False,
        'visualise': False,
        'show_sight': controller,
        'runs_no': 1,
        'profiling_metrics': [],
    }


def get_evaluator(name, neat_controller, game_runner) -> NeatEvaluator:
    if name == "eval_v1":
        return NeatEvaluatorV1(
            controller=neat_controller,
            runner=game_runner,
            cumulative=False
        )
    elif name == "eval_vt1":
        return NeatEvaluatorVT1(
            controller=neat_controller,
            runner=game_runner,
            cumulative=False
        )
    else:
        raise ValueError(f"{name} evaluator doesn't exist")


def eval_genomes_with_evaluator(evaluator_name, genomes, config):
    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        neat_controller = KimDzongNeatJuniorController(net=net)

        game_config = default_game_configuration(neat_controller)
        game_runner = runner.Runner(game_config)
        game_runner.run()

        evaluator = get_evaluator(evaluator_name, neat_controller, game_runner)

        genome.fitness += evaluator.calculate_score()

def eval_genomes_with_by_tick(evaluator_name, genomes, config, ticks_per_update=1):
    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        neat_controller = KimDzongNeatJuniorController(net=net)

        game_config = default_game_configuration(neat_controller)
        game_runner = runner.Runner(game_config)
        evaluator = get_evaluator(evaluator_name, neat_controller, game_runner)
        
        arena = classic_random.choice(game_runner.arenas)
        game = games.Game(
            game_no=0,
            arena_name=arena,
            to_spawn=game_runner.controllers,
        )
        tick_count = 0
        
        play = True
        while play:
            game.cycle()
            tick_count += 1
            if game.finished:
                play = False
            if tick_count % ticks_per_update == 0 or not play:
                game_runner._last_arena = game.arena.name
                game_runner._last_menhir_position = game.arena.menhir_position
                game_runner._last_initial_positions = game.initial_champion_positions
                score = evaluator.calculate_score(game, ticks_per_update)
                genome.fitness += score
        game_runner._last_arena = game.arena.name
        game_runner._last_menhir_position = game.arena.menhir_position
        game_runner._last_initial_positions = game.initial_champion_positions


def run_neat_training(config: neat.Config, n: int, evaluator_name: str, turns_to_update: int):
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    population.add_reporter(neat.StatisticsReporter())

    if turns_to_update < 1:
        eval_genomes = lambda genomes, neat_config: eval_genomes_with_evaluator(evaluator_name, genomes, neat_config)
    else:
        eval_genomes = lambda genomes, neat_config: eval_genomes_with_by_tick(evaluator_name, genomes, neat_config, turns_to_update)
    winner = population.run(eval_genomes, n)
    return winner
