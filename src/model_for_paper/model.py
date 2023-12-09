from src.prob import random_variable


class NonTargetServer:
    def __init__(
        self,
        packet_arrival_rate: float,
        attack_window_length: float,
        num_target_packets: int,
    ):
        self.packet_arrival_rate = packet_arrival_rate
        self.attack_window_length = attack_window_length
        self.num_target_packets = num_target_packets

    def prob_active(self) -> float:
        """A candidate server is identified as "active" during an attack window,
        only if it receives at least `num_target_packets` many packets.
        """

        num_arrivals_rv = random_variable.Poisson(
            mu=self.attack_window_length * self.packet_arrival_rate
        )
        return num_arrivals_rv.tail_prob(self.num_target_packets)

    def prob_error(
        self,
        num_attack_rounds: int,
        threshold_to_identify_as_target: float,
    ) -> random_variable.RandomVariable:
        """Returns the probability that a non-target server is identified as
        a target.
        """

        prob_active = self.prob_active()
        rv = random_variable.Binomial(
            n=num_attack_rounds,
            p=prob_active,
        )

        return rv.tail_prob(threshold_to_identify_as_target)
