from src.debug_utils import log, DEBUG, INFO
from src.prob import random_variable


class CandidateServer:
    def __init__(
        self,
        non_target_arrival_rate: float,
        attack_window_length: float,
        num_target_packets: int,
    ):
        self.non_target_arrival_rate = non_target_arrival_rate
        self.attack_window_length = attack_window_length
        self.num_target_packets = num_target_packets


class NonTargetServer(CandidateServer):
    def __init__(
        self,
        non_target_arrival_rate: float,
        attack_window_length: float,
        num_target_packets: int,
    ):
        super().__init__(
            non_target_arrival_rate=non_target_arrival_rate,
            attack_window_length=attack_window_length,
            num_target_packets=num_target_packets,
        )

        self.num_non_target_arrivals_rv = random_variable.Poisson(
            mu=self.attack_window_length * self.non_target_arrival_rate
        )
        self._prob_active = self.prob_active()

    def prob_active(self) -> float:
        """A candidate server is identified as "active" during an attack window,
        only if it receives at least `num_target_packets` many packets.
        """
        return self.num_non_target_arrivals_rv.tail_prob(self.num_target_packets)

    def prob_error(
        self,
        num_attack_rounds: int,
        threshold_to_identify_as_target: float,
    ) -> float:
        """Returns the probability that a non-target server is identified as target.
        """
        rv = random_variable.Binomial(
            n=num_attack_rounds,
            p=self._prob_active,
        )
        return rv.tail_prob(num_attack_rounds * threshold_to_identify_as_target)


class TargetServer(CandidateServer):
    def __init__(
        self,
        non_target_arrival_rate: float,
        attack_window_length: float,
        num_target_packets: int,
        num_target_servers: int,
    ):
        super().__init__(
            non_target_arrival_rate=non_target_arrival_rate,
            attack_window_length=attack_window_length,
            num_target_packets=num_target_packets,
        )
        self.num_target_servers = num_target_servers

        self.num_non_target_arrivals_rv = random_variable.Poisson(
            mu=self.attack_window_length * self.non_target_arrival_rate
        )
        self._prob_active = self.prob_active()

    def prob_active(self) -> float:
        """A candidate server is identified as "active" during an attack window,
        only if it receives at least `num_target_packets` many packets.
        """

        num_target_arrivals_rv = random_variable.Binomial(
            n=self.num_target_servers,
            p=1 / self.num_target_servers,
        )

        prob_active = 0
        for num_target_arrivals in range(self.num_target_packets + 1):
            prob_num_target_arrivals = num_target_arrivals_rv.pdf(num_target_arrivals)
            min_non_target_arrivals_for_active = self.num_target_packets - num_target_arrivals

            prob_active += prob_num_target_arrivals * self.num_non_target_arrivals_rv.tail_prob(
                min_non_target_arrivals_for_active
            )

        return prob_active

    def prob_error(
        self,
        num_attack_rounds: int,
        threshold_to_identify_as_target: float,
    ) -> float:
        """Returns the probability that a target server is identified as non-target.
        """
        rv = random_variable.Binomial(
            n=num_attack_rounds,
            p=self._prob_active,
        )
        # log(
        #     INFO, "",
        #     num_attack_rounds_X_threshold_to_identify_as_target=num_attack_rounds * threshold_to_identify_as_target,
        # )
        return rv.cdf(num_attack_rounds * threshold_to_identify_as_target)


def get_detection_threshold(
    non_target_arrival_rate: float,
    attack_window_length: float,
    num_target_packets: int,
    num_target_servers: int,
    alpha: float = 0.5,
) -> float:
    target_server = TargetServer(
        non_target_arrival_rate=non_target_arrival_rate,
        attack_window_length=attack_window_length,
        num_target_packets=num_target_packets,
        num_target_servers=num_target_servers,
    )
    prob_target_active = target_server.prob_active()

    non_target_server = NonTargetServer(
        non_target_arrival_rate=non_target_arrival_rate,
        attack_window_length=attack_window_length,
        num_target_packets=num_target_packets,
    )
    prob_non_target_active = non_target_server.prob_active()

    log(
        INFO, "",
        prob_target_active=prob_target_active,
        prob_non_target_active=prob_non_target_active,
    )

    return (
        prob_non_target_active + (prob_target_active - prob_non_target_active) * alpha
    )
