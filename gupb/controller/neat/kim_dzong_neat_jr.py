from typing import Tuple

from gupb import controller
from gupb.controller.neat import const
from gupb.controller.neat.model_config import NeatConfig
from gupb.model import arenas
from gupb.model import characters
from gupb.model.characters import Facing
from gupb.model.coordinates import Coords
from gupb.model.tiles import TileDescription

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

        self.menhir_seen = False
        self.menhir_position = None
        self.explored_area = set()

        self.are_attributes_initialized = False
        self.last_health = None
        self.last_number_of_champions_alive = None
        self.last_mist_distance = 23

        self.is_opponent_up_front = False

        self.visited_tiles = set()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, KimDzongNeatJuniorController):
            return self.first_name == other.first_name
        return False

    def __hash__(self) -> int:
        return hash(self.first_name)

    def decide(self, knowledge: characters.ChampionKnowledge) -> characters.Action:
        inputs = self.get_from_knowledge(knowledge)
        self.adjust_fitness(knowledge)
        output = self.net.activate(inputs)
        best_output_value = max(output)
        best_index = output.index(best_output_value)

        if self.is_opponent_up_front and best_index == 0:
            self.fitness += 30

        return const.POSSIBLE_ACTIONS[best_index]

    def does_make_step(self, action: characters.Action) -> bool:
        return (action == characters.Action.STEP_BACKWARD
                or action == characters.Action.STEP_FORWARD)

    def praise(self, score: int) -> None:
        '''
        Powinna byc odpowiedzialan za reakcję agenta na wynik gry ( nagradzanie lub karanie w oparciu o wynik)
        '''
        pass

    def reset(self, game_no: int, arena_description: arenas.ArenaDescription) -> None:
        '''
        Resetujemy gdy agent zayczną nową grę
        '''
        self.ticks_survived_with_mist = 0
        self.fitness = 0
        self.menhir_seen = False
        self.menhir_position = None
        self.explored_area = set()

        self.are_attributes_initialized = False
        self.last_health = None
        self.last_number_of_champions_alive = None
        self.last_mist_distance = 23
        self.visited_tiles = set()

    @property
    def name(self) -> str:
        return self.first_name

    @property
    def preferred_tabard(self) -> characters.Tabard:
        return characters.Tabard.KIMDZONGNEAT

    def adjust_fitness(self, knowledge: characters.ChampionKnowledge):
        fitness_to_adjust = 0

        number_of_visited_tiles_before = len(self.visited_tiles)
        self.visited_tiles.add(knowledge.position)
        fitness_to_adjust += self.award_for_exploration(number_of_visited_tiles_before)
        self.handle_menhir_reward(knowledge.position)


        self.fitness += fitness_to_adjust

    def handle_menhir_reward(self, player_position: Coords) -> None:
        if self.menhir_position is not None:
            distance = self.manhattan_distance(player_position, self.menhir_position)
            if distance <= 4:
                self.fitness += 20

    def get_from_knowledge(self, knowledge: characters.ChampionKnowledge):
        # fitness_to_adjust = 0
        if not self.are_attributes_initialized:
            self.initialize_attributes(knowledge)

        inputs = []
        # self.ticks_survived_with_mist += 1

        my_x, my_y = knowledge.position.x, knowledge.position.y
        # self.last_position = knowledge.position
        # fitness_to_adjust += self.award_for_health(knowledge.visible_tiles[knowledge.position].character.health)

        # number_of_visited_tiles = len(self.visited_tiles)
        # self.visited_tiles.add(knowledge.position)
        # self.fitness += (len(self.visited_tiles) - number_of_visited_tiles) * 10

        is_mist_visible = 0
        min_distance_mist = 46
        final_dx_mist = 23
        final_dy_mist = 23

        is_loot_visible = 0
        min_distance_loot = 46
        final_dx_loot = 23
        final_dy_loot = 23

        menhir_distance_x = 23
        menhir_distance_y = 23

        moves_availability = self.get_moves_availability(knowledge)
        can_go_forward = moves_availability['can_go_forward']
        can_go_left = moves_availability['can_go_left']
        can_go_right = moves_availability['can_go_right']

        champion_desc = knowledge.visible_tiles[knowledge.position].character
        forward = knowledge.position + champion_desc.facing.value
        tile = knowledge.visible_tiles[forward]
        self.handle_opponent_up_front(tile)

        for coord, tile in knowledge.visible_tiles.items():
            menhir_award, ok = self.award_for_menhir(tile)
            if ok:
                # self.fitness += menhir_award
                self.menhir_position = Coords(x=coord[0], y=coord[1])

            if self.menhir_seen:
                menhir_distance_x = my_x - self.menhir_position.x
                menhir_distance_y = my_y - self.menhir_position.y


            distance = self.manhattan_distance(knowledge.position, coord)
            if any(effect.type.lower() == const.MIST_EFFECT_TYPE for effect in tile.effects) and distance < min_distance_mist:
                is_mist_visible = 1
                final_dx_mist = my_x - coord[0]
                final_dy_mist = my_y - coord[1]
                min_distance_mist = distance
            if tile.loot is not None and distance < min_distance_loot:
                is_loot_visible = 1
                final_dx_loot = my_x - coord[0]
                final_dy_loot = my_y - coord[1]
                min_distance_loot = distance

        # self.fitness += fitness_to_adjust


        # self.fitness += self.award_knowledge_about_mist(is_mist_visible > 0)
        # self.fitness += self.award_mist_distance_change(min_distance_mist)

        # inputs.append(is_mist_visible)
        # inputs.append(final_dx_mist / 23)
        # inputs.append(final_dy_mist / 23)
        # inputs.append(is_loot_visible)
        # inputs.append(final_dx_loot / 23)
        # inputs.append(final_dy_loot / 23)
        inputs.append(can_go_forward)
        inputs.append(can_go_left)
        inputs.append(can_go_right)
        inputs.append(1) if self.menhir_seen else inputs.append(0)
        inputs.append(menhir_distance_x / 23)
        inputs.append(menhir_distance_y / 23)
        inputs.append(1) if self.is_opponent_up_front else inputs.append(0)

        return inputs

    def handle_opponent_up_front(self, up_front_tile: TileDescription):
        if up_front_tile is not None and up_front_tile.character is not None:
            self.is_opponent_up_front = True
        else:
            self.is_opponent_up_front = False

    def manhattan_distance(self, position1: Coords, position2: Coords):
        return abs(position1[0] - position2[0]) + abs(position1[1] - position2[1])

    def get_moves_availability(self, knowledge: characters.ChampionKnowledge) -> dict[str, int]:
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

    def initialize_attributes(self, knowledge: characters.ChampionKnowledge):
        champion_desc = knowledge.visible_tiles[knowledge.position].character
        self.last_health = champion_desc.health
        self.last_number_of_champions_alive = knowledge.no_of_champions_alive
        self.are_attributes_initialized = True

    def award_for_exploration(self, number_of_visited_tiles_before: int):
        return (len(self.visited_tiles) - number_of_visited_tiles_before) * 10

    def award_for_menhir(self, tile: TileDescription) -> (int, bool):
        if not self.menhir_seen and tile.type == 'menhir':
            self.menhir_seen = True
            return 100, True
        return 0, False

    def award_mist_distance_change(self, mist_distance: int):
        distances_difference = mist_distance - self.last_mist_distance
        self.last_mist_distance = mist_distance
        return distances_difference * 5

    def award_knowledge_about_mist(self, see_mist: bool):
       if see_mist:
           return 5
       return 0

    def award_for_health(self, health: int):
        health_difference = health - self.last_health
        self.last_health = health
        return health_difference * 10

    def award_for_other_player_death(self, number_of_players: int):
        if number_of_players < self.last_number_of_champions_alive:
            self.last_number_of_champions_alive = number_of_players
            return 100
        return 0

    def award_for_death(self, is_champion_alive: bool):
        if not is_champion_alive:
            return -100
        return 0


