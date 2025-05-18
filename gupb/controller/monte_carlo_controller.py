import os
import pickle
import random
from dataclasses import dataclass
from typing import NamedTuple

from gupb import controller
from gupb.model import arenas, characters, coordinates, effects, tiles

POSSIBLE_ACTIONS = [
    characters.Action.TURN_LEFT,
    characters.Action.TURN_RIGHT,
    characters.Action.STEP_FORWARD,
    characters.Action.STEP_BACKWARD,
    characters.Action.STEP_LEFT,
    characters.Action.STEP_RIGHT,
    characters.Action.DO_NOTHING,
    characters.Action.ATTACK,
]


@dataclass(frozen=True)
class MCTile:
    coords: coordinates.Coords
    is_champion: bool
    is_consumable: bool
    is_mist: bool
    is_menhir: bool
    can_move_to: bool

    @staticmethod
    def create(tile: tuple[coordinates.Coords, tiles.TileDescription]) -> "MCTile":
        coord, desc = tile

        is_mist = any(isinstance(effect, effects.Mist) for effect in desc.effects)

        return MCTile(
            coords=coord,
            is_champion=desc.character is not None,
            is_consumable=desc.consumable is not None,
            is_mist=is_mist,
            is_menhir=desc.type.lower() == "menhir",
            can_move_to=desc.type.lower() not in {"wall", "sea"},
        )


class HashableChampionKnowledge(NamedTuple):
    position: coordinates.Coords
    facing: characters.Facing
    visible_tiles: frozenset[MCTile]

    @staticmethod
    def to_hashable(
        knowledge: characters.ChampionKnowledge,
    ) -> "HashableChampionKnowledge":
        mc_tiles = get_closest_tiles(knowledge)
        me = knowledge.visible_tiles.get(knowledge.position).character
        if me is not None:
            # Czy to oks?
            facing = me.facing
        else:
            facing = None

        return HashableChampionKnowledge(
            facing=facing,
            position=knowledge.position,
            visible_tiles=frozenset(mc_tiles),
        )


def get_closest_tiles(
    champ_knowledge: characters.ChampionKnowledge, count: int = 10
) -> tuple[MCTile, ...]:
    pos = champ_knowledge.position
    mc_tiles = [MCTile.create(item) for item in champ_knowledge.visible_tiles.items()]
    mc_tiles.sort(
        key=lambda tile: abs(tile.coords[0] - pos[0]) + abs(tile.coords[1] - pos[1])
    )

    return tuple(mc_tiles[: min(len(mc_tiles), count)])


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class MonteCarloController(controller.Controller):
    def __init__(
        self,
        first_name: str = "...",
        with_policy=False,
        training=False,
        model_name="mc_policy.pkl",
        save_model=False,
    ):
        self.save_model = save_model
        self.first_name: str = first_name
        self.eps = 0.25
        self.gamma = 0.95
        self.states_history: list[HashableChampionKnowledge] = []
        self.action_history: list[characters.Action] = []
        self.training = training
        self.model_name = model_name

        self.visited_positions = set()

        if not with_policy:
            self.q: dict[tuple[HashableChampionKnowledge, characters.Action], float] = (
                {}
            )

            self.policy: dict[
                HashableChampionKnowledge, dict[characters.Action, float]
            ] = {}
            self.returns_sum: dict[
                tuple[HashableChampionKnowledge, characters.Action], float
            ] = {}
            self.returns_count: dict[
                tuple[HashableChampionKnowledge, characters.Action], int
            ] = {}

        else:
            self.load_policy()

        for (state, action), count in sorted(
            self.returns_sum.items(),
            key=lambda item: item[1],
        ):
            value = self.returns_sum[(state, action)]
            print(f"action: {action}, count: {count}, value: {value}")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MonteCarloController):
            return self.first_name == other.first_name
        return False

    def __hash__(self) -> int:
        return hash(self.first_name)

    def decide(self, knowledge: characters.ChampionKnowledge) -> characters.Action:
        self.visited_positions.add(knowledge.position)
        knowledge = HashableChampionKnowledge.to_hashable(knowledge)
        action = self.choose_action_mc(knowledge)

        self.states_history.append(knowledge)
        self.action_history.append(action)
        return action

    def praise(self, score: int) -> None:
        self.calculate_praise(score)
        self.update_policy()

    def reset(self, game_no: int, arena_description: arenas.ArenaDescription) -> None:
        self.states_history.clear()
        self.action_history.clear()

        if self.training and game_no % 3 == 0 and game_no != 0 and self.save_model:
            self.save_policy()

    @property
    def name(self) -> str:
        return f"MonteCarloController{self.first_name}"

    @property
    def preferred_tabard(self) -> characters.Tabard:
        return characters.Tabard.MCFACE

    def choose_action_mc(
        self, knowledge: HashableChampionKnowledge
    ) -> characters.Action:
        if knowledge not in self.policy:
            return random.choice(POSSIBLE_ACTIONS)

        action_probs = self.policy[knowledge]
        actions = list(action_probs.keys())
        probs = list(action_probs.values())

        if self.training:
            actions = list(action_probs.keys())
            probs = list(action_probs.values())
            return random.choices(actions, weights=probs)[0]
        else:
            return max(action_probs.items(), key=lambda item: item[1])[0]

    def calculate_praise(self, score):
        termination = len(self.states_history)
        stagnation_counter = 0

        for t, (state, action) in enumerate(
            zip(self.states_history, self.action_history)
        ):
            g_t = score * (self.gamma ** (termination - t - 1))

            if (
                t > 0
                and self.states_history[t].position
                == self.states_history[t - 1].position
            ):
                stagnation_counter += 1
                g_t -= stagnation_counter * 0.5
            else:
                stagnation_counter = 0

            key = (state, action)
            self.returns_sum[key] = self.returns_sum.get(key, 0.0) + g_t
            self.returns_count[key] = self.returns_count.get(key, 0) + 1

            self.q[key] = self.returns_sum[key] / self.returns_count[key]

    def update_policy(self):
        for state in self.states_history:
            actions = [a for (s, a) in self.q if s == state]
            if not actions:
                continue

            q_values = {a: self.q.get((state, a), 0.0) for a in actions}
            max_q = max(q_values.values())

            best_actions = [a for a, q in q_values.items() if q == max_q]
            n = len(actions)

            self.policy[state] = {}

            for a in actions:
                if a in best_actions:
                    self.policy[state][a] = (1 - self.eps) / len(
                        best_actions
                    ) + self.eps / n
                else:
                    self.policy[state][a] = self.eps / n

    def save_policy(self):
        filename = self.model_name
        q_serializable = {
            (state, action.name): value for (state, action), value in self.q.items()
        }
        policy_serializable = {
            state: {action.name: prob for action, prob in actions.items()}
            for state, actions in self.policy.items()
        }
        returns_sum_serializable = {
            (state, action.name): value
            for (state, action), value in self.returns_sum.items()
        }
        returns_count_serializable = {
            (state, action.name): value
            for (state, action), value in self.returns_count.items()
        }

        with open(filename, "wb") as f:
            pickle.dump(
                {
                    "q": q_serializable,
                    "policy": policy_serializable,
                    "returns_sum": returns_sum_serializable,
                    "returns_count": returns_count_serializable,
                },
                f,
            )

    def load_policy(self):
        filename = self.model_name
        if not os.path.exists(filename):
            print(f"Policy file {filename} not found.")
            return

        with open(filename, "rb") as f:
            data = pickle.load(f)

            self.q = {
                (state, characters.Action[action_name]): value
                for (state, action_name), value in data["q"].items()
            }
            self.policy = {
                state: {
                    characters.Action[action_name]: prob
                    for action_name, prob in actions.items()
                }
                for state, actions in data["policy"].items()
            }
            self.returns_sum = {
                (state, characters.Action[action_name]): value
                for (state, action_name), value in data["returns_sum"].items()
            }
            self.returns_count = {
                (state, characters.Action[action_name]): value
                for (state, action_name), value in data["returns_count"].items()
            }
