from abc import abstractmethod

from typing_extensions import override

from gupb import runner
from gupb.controller.neat.kim_dzong_neat_jr import KimDzongNeatJuniorController, EvaluationData
from gupb.model import games, weapons


class NeatEvaluator:
    def __init__(self, controller: KimDzongNeatJuniorController, runner: runner.Runner, cumulative: bool):
        self.controller = controller
        self.runner = runner
        self.cumulative = cumulative

    @abstractmethod
    def calculate_score(self, game: games.Game = None, tick_count: int = 0):
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
            'bow': 0.2,
            'amulet': 0.06,
            'scroll': 0.06,
        }
        self.was_death = False

    @override
    def calculate_score(self, game: games.Game = None, tick_count: int = 1):
        assert game is not None, "Game must be provided to calculate score"
        current_score = 0
        neat_controller = self.controller
        bonuses = self.bonuses
        cumulative = self.cumulative

        for champion in game.champions:
            if champion.controller == neat_controller:
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


class NeatDistanceEvaluator(NeatEvaluator):
    def __init__(self, controller: KimDzongNeatJuniorController, runner: runner.Runner, cumulative: bool):
        super().__init__(controller, runner, cumulative)
        self.weights = {
            "enemy_distance": 0.2,
            "fog_distance": 0.8,
            "fog_penalty": 7,
            "weapon_distance": -0.5,
            "potion_distance": -0.6,
            "exploration_rate": 1.5,
            "no_moving_penalty": -1,
            "ticks_live": 1,
            "step_weapon_bonus": 15,
            "step_potion_bonus": 50,
            "move_reward": 10,
            "turn_reward": 3
        }

    def calculate_score(self, game: games.Game = None, tick_count: int = 0):
        champion = self.get_my_champion(game)
        evaluation_data: EvaluationData = self.controller.evaluation_data


        if evaluation_data is None:
            # print(f"data is None : {tick_count}")
            return 0

        moved = champion.position != evaluation_data.prev_pos


        # dist_character = evaluation_data.calculate_distance_to_character(champion.position)
        dist_fog = evaluation_data.calculate_distance_to_fog(champion.position)
        dist_weapon = evaluation_data.calculate_distance_to_weapon(champion.position)
        dist_potion = evaluation_data.calculate_distance_to_potion(champion.position)

        weapon_bonus = self.weights["step_weapon_bonus"] if dist_weapon == 0 else 0
        potion_bonus = self.weights["step_potion_bonus"] if dist_potion == 0 else 0
        potion_dist_bonus = dist_potion if dist_potion < 500 else 0

        fog_penalty = self.weights["fog_penalty"] if dist_fog < 3 else 0

        return (
            # self.weights["weapon_distance"] * dist_weapon
            #     self.weights["potion_distance"] * dist_potion
                potion_dist_bonus
                + self.weights["no_moving_penalty"] * (1 - moved)
                + self.weights["exploration_rate"] * len(evaluation_data.explored_positions)
                + weapon_bonus
                + potion_bonus
                + self.weights["move_reward"] * moved
                + self.weights["turn_reward"] * evaluation_data.turned
                - fog_penalty
        )

    def get_my_champion(self, game: games.Game):
        for champion in game.champions:
            if champion.controller == self.controller:
                return champion

        return None
