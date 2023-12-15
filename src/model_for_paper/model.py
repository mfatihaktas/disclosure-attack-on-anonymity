import dataclasses
import enum
import math

from typing import Optional

from src.debug_utils import check, log, DEBUG, INFO
from src.prob import random_variable


class SamplingDist(enum.Enum):
    BINOMIAL = "binomial"
    GAUSSIAN = "gaussian"


# SAMPLING_DIST = SamplingDist.BINOMIAL
SAMPLING_DIST = SamplingDist.GAUSSIAN


@dataclasses.dataclass
class CandidateServer:
    non_target_arrival_rate: float
    attack_window_length: float
    num_target_packets: int

    def __post_init__(self):
        self.num_non_target_arrivals_rv = random_variable.Poisson(
            mu=self.attack_window_length * self.non_target_arrival_rate
        )
        self.prob_active_in_attack_win = self.get_prob_active_in_attack_win()
        self.prob_active_in_baseline_win = self.get_prob_active_in_baseline_win()

        log(
            INFO, "",
            prob_active_in_attack_win=self.prob_active_in_attack_win,
            prob_active_in_baseline_win=self.prob_active_in_baseline_win,
        )

    def get_prob_active_in_baseline_win_w_num_packets_to_deem_active(
        self,
        num_packets_to_deem_active: float,
    ) -> float:
        return self.num_non_target_arrivals_rv.tail_prob(num_packets_to_deem_active - 1)

    def _gaussian_sampling_dist(
        self,
        num_attack_rounds: int,
    ) -> random_variable.Normal:
        sigma = (
            math.sqrt(self.prob_active_in_attack_win * (1 - self.prob_active_in_attack_win))
            / math.sqrt(num_attack_rounds)
        )
        return random_variable.Normal(
            mu=self.prob_active_in_attack_win,
            sigma=sigma,
        )

    def prob_error(
        self,
        num_attack_rounds: int,
        threshold_to_identify_as_target: float,
    ) -> float:
        if SAMPLING_DIST == SamplingDist.BINOMIAL:
            return self._prob_error_w_binomial_sampling_dist(
                num_attack_rounds=num_attack_rounds,
                threshold_to_identify_as_target=threshold_to_identify_as_target,
            )

        elif SAMPLING_DIST == SamplingDist.GAUSSIAN:
            return self._prob_error_w_gaussian_sampling_dist(
                num_attack_rounds=num_attack_rounds,
                threshold_to_identify_as_target=threshold_to_identify_as_target,
            )

    def _gaussian_sampling_rv_for_detection_w_baseline(
        self,
        num_attack_rounds: int,
    ) -> random_variable.RandomVariable:
        mu = self.prob_active_in_attack_win - self.prob_active_in_baseline_win
        check(mu >= 0, "")

        var_attack_win = (
            self.prob_active_in_attack_win * (1 - self.prob_active_in_attack_win)
            / num_attack_rounds
        )
        var_baseline_win = (
            self.prob_active_in_baseline_win * (1 - self.prob_active_in_baseline_win)
            / num_attack_rounds / self.num_baseline_wins_per_attack_win
        )
        sigma = math.sqrt(var_attack_win + var_baseline_win)

        return random_variable.Normal(
            mu=mu,
            sigma=sigma if sigma else 0.000001,
        )


@dataclasses.dataclass
class NonTargetServer(CandidateServer):
    def get_prob_active_in_attack_win(self) -> float:
        """A candidate server is identified as "active" during an attack window,
        only if it receives at least `num_target_packets` many packets.
        """
        return self.num_non_target_arrivals_rv.tail_prob(self.num_target_packets - 1)

    def _prob_error_w_gaussian_sampling_dist(
        self,
        num_attack_rounds: int,
        threshold_to_identify_as_target: float,
    ) -> float:
        sampling_rv = self._gaussian_sampling_dist(
            num_attack_rounds=num_attack_rounds,
        )
        return sampling_rv.tail_prob(threshold_to_identify_as_target)

    def _prob_error_w_binomial_sampling_dist(
        self,
        num_attack_rounds: int,
        threshold_to_identify_as_target: float,
    ) -> float:
        rv = random_variable.Binomial(
            n=num_attack_rounds,
            p=self.prob_active_in_attack_win,
        )
        return rv.tail_prob(num_attack_rounds * threshold_to_identify_as_target)


@dataclasses.dataclass
class TargetServer(CandidateServer):
    num_target_servers: int

    def get_prob_active_in_attack_win_w_num_packets_to_deem_active(
        self,
        num_packets_to_deem_active: int,
    ) -> float:
        """A candidate server is deemed "active" during an attack window,
        only if it receives at least `num_packets_to_deem_active` many packets.
        """
        if self.num_target_servers == 1:
            return 1

        else:
            num_target_arrivals_rv = random_variable.Binomial(
                n=self.num_target_packets,
                p=1 / self.num_target_servers,
            )

            prob_active_in_attack_win = 0
            for num_target_arrivals in range(self.num_target_packets + 1):
                prob_num_target_arrivals = num_target_arrivals_rv.pdf(num_target_arrivals)
                min_non_target_arrivals_for_active = max(0, num_packets_to_deem_active - num_target_arrivals)

                prob_active_in_attack_win += (
                    prob_num_target_arrivals
                    * (
                        self.num_non_target_arrivals_rv.tail_prob(
                            min_non_target_arrivals_for_active - 1
                        ) if min_non_target_arrivals_for_active > 0 else 1
                    )
                )
                # log(
                #     INFO, "",
                #     prob_num_target_arrivals=prob_num_target_arrivals,
                #     num_non_target_arrivals_rv_tail_prob=self.num_non_target_arrivals_rv.tail_prob(
                #         min_non_target_arrivals_for_active - 1
                #     ),
                # )

            # log(
            #     INFO, "***",
            #     prob_active_in_attack_win=prob_active_in_attack_win,
            #     prob_active_in_baseline_win=self.num_non_target_arrivals_rv.tail_prob(
            #         num_packets_to_deem_active - 1
            #     ),
            # )
            return prob_active_in_attack_win

    def _get_prob_active_in_attack_win(self) -> float:
        """A candidate server is deemed "active" during an attack window,
        only if it receives at least one packet.
        """

        if self.num_target_servers == 1:
            return 1

        else:
            num_target_arrivals_rv = random_variable.Binomial(
                n=self.num_target_packets,
                p=1 / self.num_target_servers,
            )

            prob_at_least_one_target_arrival = num_target_arrivals_rv.tail_prob(0)
            prob_at_least_one_non_target_arrival = self.num_non_target_arrivals_rv.tail_prob(0)
            return (
                prob_at_least_one_target_arrival
                + (1 - prob_at_least_one_target_arrival) * prob_at_least_one_non_target_arrival
            )

    def _prob_error_w_binomial_sampling_dist(
        self,
        num_attack_rounds: int,
        threshold_to_identify_as_target: float,
    ) -> float:
        rv = random_variable.Binomial(
            n=num_attack_rounds,
            p=self.prob_active_in_attack_win,
        )
        # log(
        #     INFO, "",
        #     num_attack_rounds_X_threshold_to_identify_as_target=num_attack_rounds * threshold_to_identify_as_target,
        # )
        return rv.cdf(num_attack_rounds * threshold_to_identify_as_target)

    def _prob_error_w_gaussian_sampling_dist(
        self,
        num_attack_rounds: int,
        threshold_to_identify_as_target: float,
    ) -> float:
        sampling_rv = self._gaussian_sampling_dist(
            num_attack_rounds=num_attack_rounds,
        )
        return sampling_rv.cdf(threshold_to_identify_as_target)


@dataclasses.dataclass
class Server_wBaseline:
    num_baseline_wins_per_attack_win: int
    num_packets_to_deem_active: Optional[int]

    def get_prob_active_in_attack_win(self) -> float:
        if self.num_packets_to_deem_active:
            return self.get_prob_active_in_attack_win_w_num_packets_to_deem_active(
                num_packets_to_deem_active=self.num_packets_to_deem_active
            )
        else:
            return self._get_prob_active_in_attack_win()

    def get_prob_active_in_baseline_win(self) -> float:
        num_packets_to_deem_active = (
            self.num_packets_to_deem_active if self.num_packets_to_deem_active else 1
        )
        return self.get_prob_active_in_baseline_win_w_num_packets_to_deem_active(
            num_packets_to_deem_active=num_packets_to_deem_active,
        )


@dataclasses.dataclass
class NonTargetServer_wBaseline(NonTargetServer, Server_wBaseline):
    def prob_error(
        self,
        num_attack_rounds: int,
        threshold_to_identify_as_target: float,
    ) -> float:
        sampling_rv = self._gaussian_sampling_rv_for_detection_w_baseline(
            num_attack_rounds=num_attack_rounds,
        )
        return sampling_rv.tail_prob(threshold_to_identify_as_target)

    def get_prob_active_in_attack_win(self) -> float:
        return self.get_prob_active_in_baseline_win()


@dataclasses.dataclass
class TargetServer_wBaseline(TargetServer, Server_wBaseline):
    def prob_error(
        self,
        num_attack_rounds: int,
        threshold_to_identify_as_target: float,
    ) -> float:
        sampling_rv = self._gaussian_sampling_rv_for_detection_w_baseline(
            num_attack_rounds=num_attack_rounds,
        )
        return sampling_rv.cdf(threshold_to_identify_as_target)


@dataclasses.dataclass
class ExpSetup:
    non_target_arrival_rate: float
    attack_window_length: float
    num_target_packets: int
    num_target_servers: int
    alpha: float

    def __post_init__(self):
        self.target_server = self.get_target_server()
        self.non_target_server = self.get_non_target_server()

        self.target_detection_threshold = self.get_detection_threshold()
        log(
            INFO, "",
            target_server=self.target_server,
            prob_target_server_active_in_attack_win=self.target_server.prob_active_in_attack_win,
            prob_target_server_active_in_baseline_win=self.target_server.prob_active_in_baseline_win,
            non_target_server=self.non_target_server,
            prob_non_target_server_active_in_attack_win=self.non_target_server.prob_active_in_attack_win,
            prob_non_target_server_active_in_baseline_win=self.non_target_server.prob_active_in_baseline_win,
            target_detection_threshold=self.target_detection_threshold,
        )

    def prob_target_as_non_target(
        self,
        num_attack_rounds: int,
    ) -> float:
        return self.target_server.prob_error(
            num_attack_rounds=num_attack_rounds,
            threshold_to_identify_as_target=self.target_detection_threshold,
        )

    def prob_non_target_as_target(
        self,
        num_attack_rounds: int,
    ) -> float:
        return self.non_target_server.prob_error(
            num_attack_rounds=num_attack_rounds,
            threshold_to_identify_as_target=self.target_detection_threshold,
        )

    def get_min_num_attack_rounds(
        self,
        max_prob_error: float,
    ) -> int:
        num_attack_rounds = 1
        while True:
            prob_target_as_non_target = self.prob_target_as_non_target(num_attack_rounds=num_attack_rounds)
            prob_non_target_as_target = self.prob_non_target_as_target(num_attack_rounds=num_attack_rounds)
            # log(
            #     INFO, "",
            #     prob_target_as_non_target=prob_target_as_non_target,
            #     prob_non_target_as_target=prob_non_target_as_target,
            # )
            if (
                prob_target_as_non_target > max_prob_error
                or prob_non_target_as_target > max_prob_error
            ):
                num_attack_rounds *= 2

            else:
                break

        left, right = 1, num_attack_rounds
        while left < right:
            mid = (left + right) // 2

            prob_target_as_non_target = self.prob_target_as_non_target(num_attack_rounds=mid)
            prob_non_target_as_target = self.prob_non_target_as_target(num_attack_rounds=mid)
            if (
                prob_target_as_non_target > max_prob_error
                or prob_non_target_as_target > max_prob_error
            ):
                left = mid + 1

            else:
                right = mid

        return left


@dataclasses.dataclass
class ExpSetup_wTargetVsNonTarget(ExpSetup):
    def get_target_server(self) -> TargetServer:
        return TargetServer(
            non_target_arrival_rate=self.non_target_arrival_rate,
            attack_window_length=self.attack_window_length,
            num_target_packets=self.num_target_packets,
            num_target_servers=self.num_target_servers,
        )

    def get_non_target_server(self) -> NonTargetServer:
        return NonTargetServer(
            non_target_arrival_rate=self.non_target_arrival_rate,
            attack_window_length=self.attack_window_length,
            num_target_packets=self.num_target_packets,
        )

    def get_detection_threshold(self) -> float:
        return (
            self.non_target_server.prob_active_in_attack_win
            + (
                self.target_server.prob_active_in_attack_win
                - self.non_target_server.prob_active_in_attack_win
            ) * self.alpha
        )


@dataclasses.dataclass
class ExpSetup_wBaseline(ExpSetup):
    num_baseline_wins_per_attack_win: int
    num_packets_to_deem_active: Optional[int] = None

    def get_target_server(self) -> TargetServer_wBaseline:
        return TargetServer_wBaseline(
            non_target_arrival_rate=self.non_target_arrival_rate,
            attack_window_length=self.attack_window_length,
            num_target_packets=self.num_target_packets,
            num_target_servers=self.num_target_servers,
            num_baseline_wins_per_attack_win=self.num_baseline_wins_per_attack_win,
            num_packets_to_deem_active=self.num_packets_to_deem_active,
        )

    def get_non_target_server(self) -> NonTargetServer_wBaseline:
        return NonTargetServer_wBaseline(
            non_target_arrival_rate=self.non_target_arrival_rate,
            attack_window_length=self.attack_window_length,
            num_target_packets=self.num_target_packets,
            num_baseline_wins_per_attack_win=1,
            num_packets_to_deem_active=self.num_packets_to_deem_active,
        )

    def get_detection_threshold(self) -> float:
        return (
            (
                self.target_server.prob_active_in_attack_win
                - self.target_server.prob_active_in_baseline_win
            ) * self.alpha
        )
