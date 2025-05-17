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
    visible_tiles: frozenset[tuple[coordinates.Coords, tiles.TileDescription]]

    @staticmethod
    def to_hashable(
        knowledge: characters.ChampionKnowledge,
    ) -> "HashableChampionKnowledge":
        def make_tile_hashable(tile: tiles.TileDescription) -> tiles.TileDescription:
            # Przekształcamy 'effects' z listy na tuple (inne pola zostają takie same)
            if isinstance(tile.effects, list):
                tile = tile._replace(effects=tuple(tile.effects))
            return tile

        # Zamieniamy każdy TileDescription na wersję z hashowalnym 'effects'
        hashable_visible_tiles = frozenset(
            (coord, make_tile_hashable(tile))
            for coord, tile in knowledge.visible_tiles.items()
        )

        return HashableChampionKnowledge(
            position=knowledge.position,
            no_of_champions_alive=knowledge.no_of_champions_alive,
            visible_tiles=hashable_visible_tiles,
        )


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class MonteCarloController(controller.Controller):
    def __init__(self, first_name: str = "...", with_policy=False):
        self.first_name: str = first_name
        self.eps = 0.3
        self.gamma = 1.0
        self.states_history: list[HashableChampionKnowledge] = []
        self.action_history: list[characters.Action] = []

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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MonteCarloController):
            return self.first_name == other.first_name
        return False

    def __hash__(self) -> int:
        return hash(self.first_name)

    def decide(self, knowledge: characters.ChampionKnowledge) -> characters.Action:
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

        self.save_policy()

    @property
    def name(self) -> str:
        return f"MonteCarloController{self.first_name}"

    @property
    def preferred_tabard(self) -> characters.Tabard:
        return characters.Tabard.WHITE

    def choose_action_mc(
        self, knowledge: HashableChampionKnowledge
    ) -> characters.Action:
        if knowledge not in self.policy:
            return random.choice(POSSIBLE_ACTIONS)

        action_probs = self.policy[knowledge]
        actions = list(action_probs.keys())
        probs = list(action_probs.values())

        return random.choices(actions, weights=probs)[0]

    def calculate_praise(self, score):
        termination = len(self.states_history)

        for t, (state, action) in enumerate(
            zip(self.states_history, self.action_history)
        ):
            g_t = score * (self.gamma ** (termination - t - 1))

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

    def save_policy(self, filename: str = "mc_policy.pkl"):
        with open(filename, "wb") as f:
            pickle.dump(
                {
                    "q": self.q,
                    "policy": self.policy,
                    "returns_sum": self.returns_sum,
                    "returns_count": self.returns_count,
                },
                f,
            )

    def load_policy(self, filename: str = "mc_policy.pkl"):
        if not os.path.exists(filename):
            print(f"Policy file {filename} not found.")
            return

        with open(filename, "rb") as f:
            data = pickle.load(f)
            self.q = data["q"]
            self.policy = data["policy"]
            self.returns_sum = data["returns_sum"]
            self.returns_count = data["returns_count"]
