import dataclasses
import pytest

from src.debug_utils import log, DEBUG, INFO
from src.model_for_paper import model


@dataclasses.dataclass
class ExpSetupParams:
    non_target_arrival_rate: float
    attack_window_length: int
    num_target_packets: int
    num_target_servers: int
    alpha: float


@pytest.fixture
def exp_setup_params() -> ExpSetupParams:
    return ExpSetupParams(
        non_target_arrival_rate=1,
        attack_window_length=2,
        num_target_packets=1,
        num_target_servers=1,
        alpha=0.5,
    )


@pytest.fixture
def exp_setup_w_target_vs_nontarget(
    exp_setup_params: ExpSetupParams,
) -> model.ExpSetup_wTargetVsNonTarget:
    return model.ExpSetup_wTargetVsNonTarget(
        non_target_arrival_rate=exp_setup_params.non_target_arrival_rate,
        attack_window_length=exp_setup_params.attack_window_length,
        num_target_packets=exp_setup_params.num_target_packets,
        num_target_servers=exp_setup_params.num_target_servers,
        alpha=exp_setup_params.alpha,
    )


@pytest.fixture
def exp_setup_w_baseline(
    exp_setup_params: ExpSetupParams,
) -> model.ExpSetup_wBaseline:
    return model.ExpSetup_wBaseline(
        non_target_arrival_rate=exp_setup_params.non_target_arrival_rate,
        attack_window_length=exp_setup_params.attack_window_length,
        num_target_packets=exp_setup_params.num_target_packets,
        num_target_servers=exp_setup_params.num_target_servers,
        alpha=exp_setup_params.alpha,
        num_baseline_wins_per_attack_win=1,
    )


@pytest.mark.parametrize(
    "max_prob_error",
    [0.3, 0.2, 0.1, 0.01, 0.001]
)
def test_exp_setup_w_target_vs_nontarget(
    exp_setup_w_target_vs_nontarget: model.ExpSetup_wTargetVsNonTarget,
    max_prob_error: float,
):
    num_attack_rounds = exp_setup_w_target_vs_nontarget.get_min_num_attack_rounds(
        max_prob_error=max_prob_error,
    )
    log(
        INFO, "",
        max_prob_error=max_prob_error,
        num_attack_rounds=num_attack_rounds,
    )


@pytest.mark.parametrize(
    "max_prob_error",
    [0.3, 0.2, 0.1, 0.01, 0.001]
)
def test_exp_setup_w_baseline(
    exp_setup_w_baseline: model.ExpSetup_wBaseline,
    max_prob_error: float,
):
    num_attack_rounds = exp_setup_w_baseline.get_min_num_attack_rounds(
        max_prob_error=max_prob_error,
    )

    prob_target_as_non_target = exp_setup_w_baseline.target_server.prob_error(
        num_attack_rounds=num_attack_rounds,
        threshold_to_identify_as_target=exp_setup_w_baseline.target_detection_threshold,
    )
    prob_non_target_as_target = exp_setup_w_baseline.non_target_server.prob_error(
        num_attack_rounds=num_attack_rounds,
        threshold_to_identify_as_target=exp_setup_w_baseline.target_detection_threshold,
    )

    log(
        INFO, "",
        max_prob_error=max_prob_error,
        num_attack_rounds=num_attack_rounds,
        prob_target_as_non_target=prob_target_as_non_target,
        prob_non_target_as_target=prob_non_target_as_target,
    )
