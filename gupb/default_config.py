from gupb.controller import keyboard
from gupb.controller import random
from gupb.controller.neat.kim_dzong_neat_jr import KimDzongNeatJuniorController

keyboard_controller = keyboard.KeyboardController()

neat = KimDzongNeatJuniorController()

CONFIGURATION = {
    'arenas': [
        'ordinary_chaos'
    ],
    'controllers': [
        neat,
        random.RandomController("Alice"),
        random.RandomController("Bob"),
        random.RandomController("Cecilia"),
        random.RandomController("Darius"),
    ],
    'start_balancing': False,
    'visualise': True,
    'show_sight': neat,
    'runs_no': 1,
    'profiling_metrics': [],
}
