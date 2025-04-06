from gupb import controller
from gupb.controller.neat.model_config import NeatConfig
from gupb.model import arenas
from gupb.model import characters
from gupb.model.coordinates import Coords

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
    network_name="nowy_network", # ENTER NETWORK NAME
    config_name="config_mat"
)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KimDzongNeatJuniorController(controller.Controller):
    def __init__(self, first_name: str = "Kim Dzong Neat v_1", net=NEAT_CONFIG.network):
        self.first_name: str = first_name
        self.net = net

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
        # print(output)
        best_index = output.index(best_output_value)

        return POSSIBLE_ACTIONS[best_index]

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

    # def get_from_knowledge(self, knowledge: characters.ChampionKnowledge):
    #     inputs = []
    #
    #     tile_type_encoding = {
    #         'land': 1,
    #         'sea': 2,
    #         'wall': 3,
    #         'forest': 4,
    #         'menhir': 5
    #     }
    #
    #     weapon_encoding = {
    #         'knife': 1,
    #         'sword': 2,
    #         'bow_loaded': 3,
    #         'bow_unloaded': 4,
    #         'axe': 5,
    #         'amulet': 6,
    #         'scroll': 7,
    #         None: 0
    #     }
    #
    #     effect_encoding = {
    #         'weapon_cut': 0,
    #         'fire': 1,
    #         'poison': 2
    #     }
    #     effect_vector_length = len(effect_encoding)
    #
    #     my_x, my_y = knowledge.position.x, knowledge.position.y
    #
    #     # Zakładamy promień widzenia 2 (czyli 5x5 wokół gracza)
    #     for dx in range(-2, 3):
    #         for dy in range(-2, 3):
    #             coord = type(knowledge.position)(x=my_x + dx, y=my_y + dy)
    #             tile = knowledge.visible_tiles.get(coord)
    #
    #             if tile:
    #                 tile_type_id = tile_type_encoding.get(tile.type.lower(), 0)
    #                 has_character = int(tile.character is not None)
    #                 has_consumable = int(tile.consumable is not None)
    #                 loot_id = weapon_encoding.get(tile.loot.name if tile.loot else None, 0)
    #
    #                 effect_vector = [0] * effect_vector_length
    #                 for effect in tile.effects:
    #                     effect_name = effect.type.lower()
    #                     if effect_name in effect_encoding:
    #                         effect_vector[effect_encoding[effect_name]] = 1
    #             else:
    #                 # Jeśli pole niewidoczne – zakładamy pustkę
    #                 tile_type_id = 0
    #                 has_character = 0
    #                 has_consumable = 0
    #                 loot_id = 0
    #                 effect_vector = [0] * effect_vector_length
    #
    #             inputs.extend([dx, dy, tile_type_id, has_character, has_consumable, loot_id] + effect_vector)
    #
    #     # Dodatkowo liczba żywych championów
    #     inputs.append(knowledge.no_of_champions_alive)
    #
    #     return inputs
        # return [0, 1]

    def get_from_knowledge(self, knowledge: characters.ChampionKnowledge):
        inputs = []
        mist_effect_type = 'mist'

        my_x, my_y = knowledge.position.x, knowledge.position.y
        min_distance = float('inf')

        for coord, tile in knowledge.visible_tiles.items():
            if any(effect.type.lower() == mist_effect_type for effect in tile.effects):
                dx = abs(coord.x - my_x)
                dy = abs(coord.y - my_y)
                distance = dx + dy  # metryka Manhattan
                if distance < min_distance:
                    min_distance = distance

        # Jeśli nie znaleziono mgły w zasięgu – zwróć jakąś dużą wartość (np. 10)
        if min_distance == float('inf'):
            min_distance = 1000.0

        # Możesz też rozważyć normalizację np. do przedziału [0, 1]
        inputs.append(min_distance / 10.0)

        return inputs

