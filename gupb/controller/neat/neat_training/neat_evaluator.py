from abc import abstractmethod

from typing_extensions import override

from gupb import runner
from gupb.controller.neat.kim_dzong_neat_jr import KimDzongNeatJuniorController
from gupb.model import games, weapons


class NeatEvaluator:
    def __init__(self, controller: KimDzongNeatJuniorController, runner: runner.Runner, cumulative: bool):
        self.controller = controller
        self.runner = runner
        self.cumulative = cumulative

    @abstractmethod
    def calculate_score(self,game: games.Game=None, tick_count: int=0):
        raise NotImplementedError("This method must be implemented in a subclass")


class NeatEvaluatorV1(NeatEvaluator):
    def __init__(self, controller: KimDzongNeatJuniorController, runner: runner.Runner, cumulative: bool):
        super().__init__(controller, runner, cumulative)

    @override
    def calculate_score(self):
        score = self.runner.scores["Kim Dzong Neat v_1"]
        print("Kim Dzong Neat v_1 score: {}".format(score))
        return score

class NeatEvaluatorVTScheme(NeatEvaluator):
    def __init__(self, controller: KimDzongNeatJuniorController, runner: runner.Runner, cumulative: bool):
        super().__init__(controller, runner, cumulative)

    @override
    def calculate_score(self, game: games.Game = None, tick_count: int=1):
        assert game is not None, "Game must be provided to calculate score"
        current_score = 0
        neat_controller = self.controller
        bonuses = self.bonuses
        cumulative = self.cumulative
        is_alive = True
        menhir_position = game.arena.menhir_position
        for champion in game.champions:
            if champion.controller == neat_controller:
                is_alive = champion.alive
                if is_alive:
                    if cumulative:
                        current_score += tick_count * bonuses['survival']
                    else:
                        current_score += bonuses['survival']
                    distance = ((champion.position.x - menhir_position.x) ** 2 + 
                                (champion.position.y - menhir_position.y) ** 2) ** 0.5
                    current_score += bonuses['distance'] / (distance + 1)  
                    current_score += champion.health * bonuses['health']
                    if hasattr(champion, 'weapon') and champion.weapon:
                        current_score += bonuses['weapon']
                        if isinstance(champion.weapon, weapons.Knife):
                            current_score += bonuses['knife']
                        elif isinstance(champion.weapon, weapons.Sword):
                            current_score += bonuses['sword']
                        elif isinstance(champion.weapon, weapons.Axe):
                            current_score += bonuses['axe']
                        elif isinstance(champion.weapon, weapons.Bow):
                            current_score += bonuses['bow']
                        elif isinstance(champion.weapon, weapons.Amulet):
                            current_score += bonuses['amulet']
                        elif isinstance(champion.weapon, weapons.Scroll):
                            current_score += bonuses['scroll']
            elif champion.alive:
                current_score += bonuses['enemy']
        if (not is_alive):
            current_score += bonuses['death']
        return current_score

class NeatEvaluatorVT1(NeatEvaluatorVTScheme):
    def __init__(self, controller: KimDzongNeatJuniorController, runner: runner.Runner, cumulative: bool):
        super().__init__(controller, runner, cumulative)
        self.bonuses = {
            'survival': 3,
            'health': 2.5,
            'enemy': -0.08,
            'death': -15,
            'weapon': 0.2,
            'knife': 0,
            'sword': 0.1,
            'axe': 0.11,
            'bow':0.3,
            'amulet':0.11,
            'scroll':0.06,
            'distance':75,
        }

    @override
    def calculate_score(self, game: games.Game = None, tick_count: int=1):
        return super().calculate_score(game, tick_count)
    
class NeatEvaluatorVT2(NeatEvaluatorVTScheme):
    def __init__(self, controller: KimDzongNeatJuniorController, runner: runner.Runner, cumulative: bool):
        super().__init__(controller, runner, cumulative)
        self.bonuses = {
            'survival': 3,
            'health': 2.5,
            'enemy': -0.08,
            'death': -150,
            'weapon': 0.2,
            'knife': -0.1,
            'sword': 0.1,
            'axe': 0.11,
            'bow':0.3,
            'amulet':0.11,
            'scroll':0.06,
            'distance':75,
        }

    @override
    def calculate_score(self, game: games.Game = None, tick_count: int=1):
        return super().calculate_score(game, tick_count)
