from abc import abstractmethod

from typing_extensions import override

from gupb import runner
from gupb.controller.neat.kim_dzong_neat_jr import KimDzongNeatJuniorController
from gupb.model import games, weapons
from gupb.model.coordinates import Coords


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

class NeatEvaluatorVT1(NeatEvaluator):
    def __init__(self, controller: KimDzongNeatJuniorController, runner: runner.Runner, cumulative: bool):
        super().__init__(controller, runner, cumulative)
        self.bonuses = {
            'survival': 0.2,
            'health': 0.5,
            'enemy': -0.05,
            'death': -150,
            'weapon': 0.1,
            'knife': 0,
            'sword': 0.05,
            'axe': 0.06,
            'bow':0.2,
            'amulet':0.06,
            'scroll':0.06,
        }
        self.was_death = False
        self.last_position = Coords(x=0, y=0)


    @override
    def calculate_score(self, game: games.Game = None, tick_count: int=1):
        assert game is not None, "Game must be provided to calculate score"
        current_score = 0
        neat_controller = self.controller
        bonuses = self.bonuses
        cumulative = self.cumulative

        for champion in game.champions:
            if champion.controller == neat_controller:
                if champion.position != self.last_position:
                    current_score += 100
                    self.last_position = champion.position
                self.was_death = False
                if cumulative:
                    current_score += tick_count * bonuses['survival']
                else:
                    current_score += bonuses['survival']
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
            else:
                current_score += bonuses['enemy']
        if (not any(champion.controller == neat_controller for champion in game.champions)) and (not self.was_death):
            self.was_death = True
            current_score += bonuses['death']
        return current_score
