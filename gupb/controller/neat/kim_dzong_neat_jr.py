from typing import Tuple

from gupb import controller
from gupb.controller.neat import const
from gupb.controller.neat.model_config import NeatConfig
from gupb.model import arenas
from gupb.model import characters
from gupb.model.characters import Facing
from gupb.model.coordinates import Coords

NEAT_CONFIG = NeatConfig(
    network_name="nowy_network",  # ENTER NETWORK NAME
    config_name="snake_config"
)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KimDzongNeatJuniorController(controller.Controller):
    def __init__(self, first_name: str = "Kim Dzong Neat v_1", net=NEAT_CONFIG.network):
        self.first_name: str = first_name
        self.net = net
        self.ticks_survived_with_mist = 0
        self.last_position = Coords(x=0, y=0)
        self.fitness = 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, KimDzongNeatJuniorController):
            return self.first_name == other.first_name
        return False

    def __hash__(self) -> int:
        return hash(self.first_name)

    def decide(self, knowledge: characters.ChampionKnowledge) -> characters.Action:
        inputs = self.get_from_knowledge(knowledge)
        output = self.net.activate(inputs)
        best_output_value = max(output)
        best_index = output.index(best_output_value)
        action = const.POSSIBLE_ACTIONS[best_index]

        if self.does_make_step(action):
            self.moves += 1

        self.adjust_fitness(action, knowledge)

        return const.POSSIBLE_ACTIONS[best_index]

    def does_make_step(self, action: characters.Action) -> bool:
        return (action == characters.Action.STEP_BACKWARD
                or action == characters.Action.STEP_FORWARD)

    def adjust_fitness(self, action: characters.Action, knowledge: characters.ChampionKnowledge):
        fitness_to_adjust = 0
        current_position = Coords(x=knowledge.position.x,
                                  y=knowledge.position.y)

        if self.does_make_step(action) or action == characters.Action.ATTACK:
            fitness_to_adjust += 1

        if self.last_position != current_position:
            fitness_to_adjust += 2
        else:
            fitness_to_adjust -= 1

        self.fitness += fitness_to_adjust

    def praise(self, score: int) -> None:
        '''
        Powinna byc odpowiedzialan za reakcję agenta na wynik gry ( nagradzanie lub karanie w oparciu o wynik)
        '''
        self.fitness += score

    def reset(self, game_no: int, arena_description: arenas.ArenaDescription) -> None:
        '''
        Resetujemy gdy agent zayczną nową grę
        '''
        self.ticks_survived_with_mist = 0
        self.moves = 0
        self.fitness = 0

    @property
    def name(self) -> str:
        return self.first_name

    @property
    def preferred_tabard(self) -> characters.Tabard:
        return characters.Tabard.KIMDZONGNEAT

    # [czy widac mgle, ile w x od najblizszej mgly, przesuniecie y od najblizszej mgly, czy widac bron, ile w x od najblizszej broni, ile w y od najblizszej broni,
    # czy może wykonać ruch do przodu, czy może wykonać ruch w lewo, czy może wykonać ruch w prawo]
    def get_from_knowledge(self, knowledge: characters.ChampionKnowledge):
        inputs = []
        self.ticks_survived_with_mist += 1

        my_x, my_y = knowledge.position.x, knowledge.position.y
        self.last_position = knowledge.position

        is_mist_visible = 0
        min_distance_mist = 46
        final_dx_mist = 23
        final_dy_mist = 23

        is_loot_visible = 0
        min_distance_loot = 46
        final_dx_loot = 23
        final_dy_loot = 23

        moves_availability = self.get_available_moves(knowledge)
        can_go_forward = moves_availability['can_go_forward']
        can_go_left = moves_availability['can_go_left']
        can_go_right = moves_availability['can_go_right']

        for coord, tile in knowledge.visible_tiles.items():
            dx = abs(coord[0] - my_x)
            dy = abs(coord[1] - my_y)
            distance = dx + dy  # metric Manhattan
            if any(effect.type.lower() == const.MIST_EFFECT_TYPE for effect in tile.effects) and distance < min_distance_mist:
                is_mist_visible = 1
                final_dx_mist = my_x - coord[0]
                final_dy_mist = my_y - coord[1]
                min_distance_mist = distance
            if tile.loot is not None and distance < min_distance_loot:
                is_loot_visible = 1
                final_dx_loot = my_x - coord[0]
                final_dy_loot = my_y - coord[1]
                min_distance_mist = distance

        inputs.append(is_mist_visible)
        inputs.append(final_dx_mist / 23)
        inputs.append(final_dy_mist / 23)
        inputs.append(is_loot_visible)
        inputs.append(final_dx_loot / 23)
        inputs.append(final_dy_loot / 23)
        inputs.append(can_go_forward)
        inputs.append(can_go_left)
        inputs.append(can_go_right)

        return inputs

    def get_available_moves(self, knowledge: characters.ChampionKnowledge) -> dict[str, int]:
        can_go_forward = 1
        can_go_left = 1
        can_go_right = 1

        champion_desc = knowledge.visible_tiles[knowledge.position].character
        fwd, lft, rgt = self.get_forwards_left_right_coords(knowledge.position, champion_desc.facing)

        if knowledge.visible_tiles[fwd].type in const.BLOCKS:
            can_go_forward = 0
        if knowledge.visible_tiles[lft].type in const.BLOCKS:
            can_go_left = 0
        if knowledge.visible_tiles[rgt].type in const.BLOCKS:
            can_go_right = 0

        return {
            "can_go_forward": can_go_forward,
            "can_go_left": can_go_left,
            "can_go_right": can_go_right
        }

    def get_forwards_left_right_coords(self, position: Coords, facing: Facing) -> Tuple[Coords, Coords, Coords]:
        forward = position + facing.value
        left = position + const.TURN_LEFT[facing].value
        right = position + const.TURN_RIGHT[facing].value

        return forward, left, right
