import numpy as np

from gupb import controller
from gupb.controller.neat.model_config import NeatConfig
from gupb.model import arenas
from gupb.model import characters
from gupb.model.effects import Mist

POSSIBLE_ACTIONS = [
    characters.Action.ATTACK,
    characters.Action.STEP_FORWARD,
    characters.Action.TURN_RIGHT,
    characters.Action.TURN_LEFT,
    characters.Action.STEP_BACKWARD,
    characters.Action.STEP_LEFT,
    characters.Action.STEP_RIGHT,
    characters.Action.DO_NOTHING,
]

NEAT_CONFIG = NeatConfig(
    network_name="dist_net_v1",  # ENTER NETWORK NAME
    config_name="config_jerzy"
)

MAX_DISTANCE = 1000
DEFAULT_POST = (MAX_DISTANCE, MAX_DISTANCE)


class EvaluationData:
    def __init__(self,
                 prev_pos,
                 closest_character_pos,
                 closest_fog_pos,
                 closest_weapon_pos,
                 closest_potion_pos,
                 explored_positions):
        self.prev_pos = prev_pos
        self.closest_character_pos = closest_character_pos
        self.closest_fog_pos = closest_fog_pos
        self.closest_weapon_pos = closest_weapon_pos
        self.closest_potion_pos = closest_potion_pos
        self.explored_positions = explored_positions
        self.turned = 0
        self.moved = 0

    def calculate_distance_to_character(self, pos):
        return calculate_distance(pos, self.closest_character_pos)

    def calculate_distance_to_fog(self, pos):
        return calculate_distance(pos, self.closest_fog_pos)

    def calculate_distance_to_weapon(self, pos):
        return calculate_distance(pos, self.closest_weapon_pos)

    def calculate_distance_to_potion(self, pos):
        return calculate_distance(pos, self.closest_potion_pos)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KimDzongNeatJuniorController(controller.Controller):
    def __init__(self, first_name: str = "Kim Dzong Neat v_1", net=NEAT_CONFIG.network):
        self.first_name: str = first_name
        self.net = net
        self.evaluation_data = None
        self.explored_positions = set()

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
        action = POSSIBLE_ACTIONS[best_index]

        if action in {characters.Action.STEP_FORWARD,
                      characters.Action.STEP_LEFT,
                      characters.Action.STEP_BACKWARD,
                      characters.Action.STEP_RIGHT}:
            self.evaluation_data.moved = 1
        else:
            self.evaluation_data.moved = 0

        if action in {characters.Action.TURN_RIGHT,
                      characters.Action.TURN_LEFT}:
            self.evaluation_data.turned = 1
        else:
            self.evaluation_data.turned = 0

        return action

    def praise(self, score: int) -> None:
        '''
        Powinna byc odpowiedzialan za reakcję agenta na wynik gry ( nagradzanie lub karanie w oparciu o wynik)
        '''
        pass

    def reset(self, game_no: int, arena_description: arenas.ArenaDescription) -> None:
        '''
        Resetujemy gdy agent zayczną nową grę
        '''
        pass

    @property
    def name(self) -> str:
        return self.first_name

    @property
    def preferred_tabard(self) -> characters.Tabard:
        return characters.Tabard.KIMDZONGNEAT

    def get_from_knowledge(self, knowledge: characters.ChampionKnowledge):
        curr_position = knowledge.position
        self.explored_positions.add(curr_position)

        closest_distance_character = MAX_DISTANCE
        closest_distance_weapon = MAX_DISTANCE
        closest_distance_potion = MAX_DISTANCE
        closest_distance_fog = MAX_DISTANCE

        see_fog = 0
        see_potion = 0
        see_weapon = 0

        closest_character_pos = DEFAULT_POST
        closest_weapon_pos = DEFAULT_POST
        closest_potion_pos = DEFAULT_POST
        closest_fog_pos = DEFAULT_POST

        for pos, tile in knowledge.visible_tiles.items():
            if tile.character is not None:
                distance = calculate_distance(curr_position, pos)
                if distance < closest_distance_character:
                    closest_distance_character = distance
                    closest_character_pos = pos

            elif tile.loot is not None:
                see_weapon = 1
                distance = calculate_distance(curr_position, pos)
                if distance < closest_distance_weapon:
                    closest_distance_weapon = distance
                    closest_weapon_pos = pos


            elif tile.consumable is not None:
                see_potion = 1
                distance = calculate_distance(curr_position, pos)
                if distance < closest_distance_potion:
                    closest_distance_potion = distance
                    closest_potion_pos = pos

            if len(tile.effects) > 0:
                for effect in tile.effects:
                    if isinstance(effect, Mist):
                        see_fog = 1
                        distance = calculate_distance(curr_position, pos)
                        if distance < closest_distance_fog:
                            closest_distance_fog = distance
                            closest_fog_pos = pos

        has_seen_anything = (closest_character_pos != DEFAULT_POST or
                             closest_fog_pos != DEFAULT_POST or
                             closest_weapon_pos != DEFAULT_POST or
                             closest_potion_pos != DEFAULT_POST)

        self.evaluation_data = EvaluationData(
            prev_pos=curr_position,
            closest_character_pos=closest_character_pos,
            closest_fog_pos=closest_fog_pos,
            closest_weapon_pos=closest_weapon_pos,
            closest_potion_pos=closest_potion_pos,
            explored_positions=self.explored_positions
        )

        return [curr_position[0], curr_position[1],
                closest_fog_pos[0], closest_fog_pos[1],
                closest_weapon_pos[0], closest_weapon_pos[1],
                closest_potion_pos[0], closest_potion_pos[1],
                see_potion, see_weapon, see_fog]


def calculate_distance(pos1, pos2):
    return np.abs(pos1[0] - pos2[0]) + np.abs(pos1[1] - pos2[1])
