import math

from src.debug_utils import check, DEBUG, ERROR, INFO, log


class Model_wRounds():
    def __init__(
        self,
        num_clients: int,
        num_servers: int,
        num_target_servers: int,
        prob_server_active: float,
        prob_attack_round: float,
    ):
        check(num_target_servers <= num_servers, "")

        self.num_clients = num_clients
        self.num_servers = num_servers
        self.num_target_servers = num_target_servers
        self.prob_server_active = prob_server_active
        self.prob_attack_round = prob_attack_round

    def __repr__(self):
        return (
            "Model_wRounds( \n"
            f"\t num_clients= {self.num_clients} \n"
            f"\t num_servers= {self.num_servers} \n"
            f"\t num_target_servers= {self.num_target_servers} \n"
            f"\t prob_server_active= {self.prob_server_active} \n"
            f"\t prob_attack_round= {self.prob_attack_round} \n"
            ")"
        )

    def prob_target_server_is_active(self) -> float:
        return (
            self.prob_target_server_is_active_given_attack_round() * self.prob_attack_round
            + self.prob_server_active * (1 - self.prob_attack_round)
        )

    def prob_target_server_is_active_given_attack_round(self) -> float:
        return (
            1 / self.num_target_servers
            + self.prob_server_active * (1 - 1 / self.num_target_servers)
        )

    def prob_nontarget_server_is_active(self) -> float:
        return self.prob_server_active

    def prob_nontarget_server_is_active_given_attack_round(self) -> float:
        return self.prob_server_active

    def max_stdev_of_prob_estimates(
        self,
        detection_gap_exp_factor: float,
    ) -> float:
        return (
            (
                self.prob_target_server_is_active_given_attack_round()
                - self.prob_target_server_is_active()
            ) / 2 / math.sqrt(2) / detection_gap_exp_factor
        )

    def detection_threshold(
        self,
        detection_gap_exp_factor: float,
    ) -> float:
        return (
            math.sqrt(2)
            * detection_gap_exp_factor
            * self.max_stdev_of_prob_estimates(
                detection_gap_exp_factor=detection_gap_exp_factor
            )
        )
