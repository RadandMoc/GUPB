from gupb import controller
from gupb.controller.neat.model_config import NeatConfig
from gupb.model import arenas
from gupb.model import characters
from gupb.model.coordinates import Coords

POSSIBLE_ACTIONS = [
    characters.Action.ATTACK,
    characters.Action.STEP_FORWARD,
    characters.Action.STEP_BACKWARD,
    characters.Action.TURN_RIGHT,
    characters.Action.TURN_LEFT,
    characters.Action.STEP_LEFT,
    characters.Action.STEP_RIGHT,
    characters.Action.DO_NOTHING,
]

NEAT_CONFIG = NeatConfig(
    network_name="nowy_network", # ENTER NETWORK NAME
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
        self.fitness = 0  # Dodajemy zmienną do przechowywania wyniku fitness


    def __eq__(self, other: object) -> bool:
        if isinstance(other, KimDzongNeatJuniorController):
            return self.first_name == other.first_name
        return False

    def __hash__(self) -> int:
        return hash(self.first_name)

    def calculate_fitness_per_tick(self, action_index: int) -> int:
        """
        Ta funkcja będzie przydzielać różne punkty na podstawie akcji agenta.
        """
        fitness = 0
        if action_index == 1 or action_index == 2 or action_index == 3:  # ATTACK
            fitness += 1
        # Dodaj inne akcje i przypisz im odpowiednią wartość
        return fitness

    def decide(self, knowledge: characters.ChampionKnowledge) -> characters.Action:
        inputs = self.get_from_knowledge(knowledge)
        output = self.net.activate(inputs)
        best_output_value = max(output)
        best_index = output.index(best_output_value)
        if best_index == 1 or best_index == 2:
            self.moves += 1

        self.fitness += self.calculate_fitness_per_tick(best_index)

        return POSSIBLE_ACTIONS[best_index]

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
    # czy może wykonać ruch do przodu, czy może wykonać ruch do tyłu]
    def get_from_knowledge(self, knowledge: characters.ChampionKnowledge):
        inputs = []
        mist_effect_type = 'mist'
        self.ticks_survived_with_mist += 1

        my_x, my_y = knowledge.position.x, knowledge.position.y
        if self.last_position != Coords(x=my_x, y=my_y):
            self.last_position = Coords(x=my_x, y=my_y)
            self.fitness += 2
        else:
            self.fitness -= 2

        is_mist = 0
        min_distance_mist = 46
        final_dx_mist = 23
        final_dy_mist = 23

        is_loot = 0
        min_distance_loot = 46
        final_dx_loot = 23
        final_dy_loot = 23

        for coord, tile in knowledge.visible_tiles.items():
            dx = abs(coord[0] - my_x)
            dy = abs(coord[1] - my_y)
            distance = dx + dy  # metryka Manhattan
            if any(effect.type.lower() == mist_effect_type for effect in tile.effects) and distance < min_distance_mist:
                is_mist = 1
                final_dx_mist = my_x - coord[0]
                final_dy_mist = my_y - coord[1]
                min_distance_mist = distance
            if tile.loot is not None and distance < min_distance_loot:
                is_loot = 1
                final_dx_loot = my_x - coord[0]
                final_dy_loot = my_y - coord[1]
                min_distance_mist = distance

        inputs.append(is_mist)
        inputs.append(final_dx_mist / 23)
        inputs.append(final_dy_mist / 23)
        inputs.append(is_loot)
        inputs.append(final_dx_loot / 23)
        inputs.append(final_dy_loot / 23)


        return inputs

