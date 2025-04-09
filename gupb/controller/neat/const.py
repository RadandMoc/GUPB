from gupb.model import characters
from gupb.model.characters import Facing

BLOCKS = {'sea', 'wall'}
MIST_EFFECT_TYPE = 'mist'

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

TURN_LEFT = {
    Facing.UP: Facing.LEFT,
    Facing.DOWN: Facing.RIGHT,
    Facing.LEFT: Facing.DOWN,
    Facing.RIGHT: Facing.UP,
}

TURN_RIGHT = {
    Facing.UP: Facing.RIGHT,
    Facing.DOWN: Facing.LEFT,
    Facing.LEFT: Facing.UP,
    Facing.RIGHT: Facing.DOWN,
}
