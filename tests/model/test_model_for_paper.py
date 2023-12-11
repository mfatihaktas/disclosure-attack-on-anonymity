import pytest

from src.debug_utils import log, DEBUG, INFO
from src.model_for_paper import model


@pytest.fixture
def exp_setup() -> model.ExpSetup:
    non_target_arrival_rate = 1
    attack_window_length = 2
    num_target_packets = 1
    num_target_servers = 1
    alpha = 0.5

    return model.ExpSetup(
        non_target_arrival_rate=non_target_arrival_rate,
        attack_window_length=attack_window_length,
        num_target_packets=num_target_packets,
        num_target_servers=num_target_servers,
        alpha=alpha,
    )


@pytest.mark.parametrize(
    "max_prob_error",
    [0.3, 0.2, 0.1, 0.01, 0.001]
)
def test_get_min_num_attack_rounds(
    exp_setup: model.ExpSetup,
    max_prob_error: float,
):
    num_attack_rounds = exp_setup.get_min_num_attack_rounds(
        max_prob_error=max_prob_error,
    )
    log(
        INFO, "",
        max_prob_error=max_prob_error,
        num_attack_rounds=num_attack_rounds,
    )
