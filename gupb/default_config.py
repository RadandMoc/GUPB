from gupb.controller import random
from gupb.controller.monte_carlo_controller import MonteCarloController

is_training = False
with_policy = True
save_model = False
training_eps = 1000
monte_carlo_controller = MonteCarloController(
    with_policy=with_policy,
    training=is_training,
    model_name="model6.pkl",
    save_model=save_model,
)

CONFIGURATION = {
    "arenas": ["ordinary_chaos"],
    "controllers": [
        monte_carlo_controller,
        random.RandomController("Alice"),
        random.RandomController("Bob"),
        random.RandomController("Cecilia"),
        random.RandomController("Darius"),
    ],
    "start_balancing": True,
    "visualise": False,
    "show_sight": monte_carlo_controller,
    "runs_no": training_eps if is_training else 100,
    "profiling_metrics": [],
}
