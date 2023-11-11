import bisect
import collections
import dataclasses
import numpy
import simpy
import sklearn.cluster

from typing import Optional

from src.attack import adversary as adversary_module
from src.prob import random_variable
from src.sim import message

from src.debug_utils import check, log, DEBUG, INFO, slog


class DisclosureAttack(adversary_module.Adversary):
    """Tries to deanonymize the (target) servers that a target client talks to.
    """

    def __init__(
        self,
        env: simpy.Environment,
        max_msg_delivery_time: float,
        error_percent: float,
    ):
        self.env = env
        self.max_msg_delivery_time = max_msg_delivery_time
        self.error_percent = error_percent

        self.server_id_to_time_epochs_msg_sent_map = collections.defaultdict(list)

        self.num_sample_sets_collected = 0
        self.server_id_to_weight_map = collections.defaultdict(float)

        self.attack_completed_event = self.env.event()

        self.target_server_id_set = None
        self.time_to_complete_attack = None

    def __repr__(self):
        return f"DisclosureAttack(error_percent= {self.error_percent})"

    def client_sent_msg(self, msg: message.Message):
        pass

    def server_recved_msg(self, msg: message.Message):
        pass

    def server_sent_msg(self, msg: message.Message):
        slog(DEBUG, self.env, self, "server sent msg")

        server_id = msg.src_id
        bisect.insort_left(
            self.server_id_to_time_epochs_msg_sent_map[server_id],
            self.env.now
        )

    def client_completed_get_request(
        self,
        num_msgs_recved_for_get_request: int,
    ):
        slog(
            INFO, self.env, self, "client completed request",
            num_msgs_recved_for_get_request=num_msgs_recved_for_get_request,
            # server_id_to_time_epochs_msg_sent_map=self.server_id_to_time_epochs_msg_sent_map,
        )

        sample_candidate_set = self.get_sample_candidate_set(
            num_msgs_recved_for_get_request=num_msgs_recved_for_get_request,
        )
        slog(
            DEBUG, self.env, self, "",
            sample_candidate_set=sample_candidate_set,
        )
        if not sample_candidate_set:
            return

        self.trim_server_id_to_time_epochs_msg_sent_map()

        # Update the attack state
        self.update(sample_candidate_set=sample_candidate_set)

        # Check if the attack is completed
        self.target_server_id_set = self.try_to_get_target_server_id_set()
        if self.target_server_id_set is not None:
            slog(
                INFO, self.env, self,
                "completed attack",
                target_server_id_set=self.target_server_id_set,
                end_of_attack_log=self.get_end_of_attack_log(),
            )
            self.time_to_complete_attack = self.env.now
            self.attack_completed_event.succeed()

    def update(self, sample_candidate_set: set[str]):
        slog(
            DEBUG, self.env, self,
            "started",
            sample_candidate_set=sample_candidate_set,
        )

        for server_id in (
            set(self.server_id_to_weight_map.keys())
            | sample_candidate_set
        ):
            weight = self.server_id_to_weight_map[server_id]
            self.server_id_to_weight_map[server_id] = (
                (
                    weight * self.num_sample_sets_collected
                    + int(server_id in sample_candidate_set)
                )
                / (self.num_sample_sets_collected + 1)
            )

        self.num_sample_sets_collected += 1
        log(
            INFO, "updated",
            num_sample_sets_collected=self.num_sample_sets_collected,
            num_sampled_candidates=len(sample_candidate_set),
            # sample_candidate_set=sample_candidate_set,
        )

    def try_to_get_target_server_id_set(self) -> Optional[set[str]]:
        if self.num_sample_sets_collected < 10:
            return None

        weight_and_server_id_list = sorted(
            [
                (weight, server_id)
                for server_id, weight in self.server_id_to_weight_map.items()
            ],
        )
        # log(INFO, "", weight_and_server_id_list=weight_and_server_id_list)

        weight_list = [w for w, _ in weight_and_server_id_list]
        for m in range(len(weight_and_server_id_list), 0, -1):
            target_weight = 1 / m
            if not (
                target_weight * (1 - self.error_percent)
                <= weight_list[-1]
                <= target_weight * (1 + self.error_percent)
            ):
                continue

            left_index = bisect.bisect_left(
                weight_list,
                target_weight * (1 - self.error_percent),
            )
            # log(INFO, "", m=m, left_index=left_index)

            if len(weight_and_server_id_list) - left_index == m:
                return set(
                    server_id
                    for (_, server_id) in weight_and_server_id_list[-m:]
                )

        return None

    def get_sample_candidate_set(
        self,
        num_msgs_recved_for_get_request: int,
    ) -> set[str]:
        min_time_epoch = self.env.now - self.max_msg_delivery_time
        sample_candidate_set = set()
        for server_id, time_epochs_msg_sent in self.server_id_to_time_epochs_msg_sent_map.items():
            if not time_epochs_msg_sent:
                continue

            first_index_smaller = bisect.bisect_left(time_epochs_msg_sent, min_time_epoch)
            log(
                DEBUG, "",
                server_id=server_id,
                min_time_epoch=min_time_epoch,
                first_index_smaller=first_index_smaller,
            )
            if len(time_epochs_msg_sent) - first_index_smaller >= num_msgs_recved_for_get_request:
                sample_candidate_set.add(server_id)

        return sample_candidate_set

    def trim_server_id_to_time_epochs_msg_sent_map(self):
        min_time_epoch = self.env.now - self.max_msg_delivery_time
        for server_id, time_epochs_msg_sent in self.server_id_to_time_epochs_msg_sent_map.items():
            left_index = bisect.bisect_left(time_epochs_msg_sent, min_time_epoch)
            self.server_id_to_time_epochs_msg_sent_map[server_id] = time_epochs_msg_sent[left_index:]


class DisclosureAttack_wBaselineInspection(DisclosureAttack):
    def __init__(
        self,
        env: simpy.Environment,
        max_msg_delivery_time: float,
    ):
        super().__init__(
            env=env,
            max_msg_delivery_time=max_msg_delivery_time,
            error_percent=None,
        )

        self.server_id_to_baseline_weight_map = collections.defaultdict(float)
        self.server_id_weight_diff_map = collections.defaultdict(float)

        self.num_baseline_sample_sets_collected = 0
        self.baseline_inspection_process = env.process(self.baseline_inspection())

    def __repr__(self):
        return "DisclosureAttack_wBaselineInspection"

    def get_end_of_attack_log(self) -> dict:
        return {
            "server_id_to_weight_map": self.server_id_to_weight_map,
            "server_id_to_baseline_weight_map": self.server_id_to_baseline_weight_map,
            "server_id_weight_diff_map": self.server_id_weight_diff_map,
        }

    def baseline_inspection(self):
        interval_rv = random_variable.Exponential(mu=2 / self.max_msg_delivery_time)

        num_msgs_recved_for_get_request = 1
        while True:
            interval = interval_rv.sample()
            slog(DEBUG, self.env, self, "waiting", interval=interval)
            yield self.env.timeout(interval)

            sample_candidate_set = self.get_sample_candidate_set(
                num_msgs_recved_for_get_request=num_msgs_recved_for_get_request,
            )
            if not sample_candidate_set:
                slog(DEBUG, self.env, self, "skipping empty sample_candidate_set")
                continue

            for server_id in (
                set(self.server_id_to_baseline_weight_map.keys())
                | sample_candidate_set
            ):
                weight = self.server_id_to_baseline_weight_map[server_id]
                self.server_id_to_baseline_weight_map[server_id] = (
                    (
                        weight * self.num_baseline_sample_sets_collected
                        + int(server_id in sample_candidate_set)
                    )
                    / (self.num_baseline_sample_sets_collected + 1)
                )

            slog(
                DEBUG, self.env, self,
                "baseline inspection round",
                num_msgs_recved_for_get_request=num_msgs_recved_for_get_request,
                sample_candidate_set=sample_candidate_set,
                num_baseline_sample_sets_collected=self.num_baseline_sample_sets_collected,
                server_id_to_baseline_weight_map=self.server_id_to_baseline_weight_map,
            )
            self.num_baseline_sample_sets_collected += 1


class DisclosureAttack_wBaselineInspection_wStationaryRounds(DisclosureAttack_wBaselineInspection):
    def __init__(
        self,
        env: simpy.Environment,
        max_msg_delivery_time: float,
        stability_threshold: float,
    ):
        super().__init__(
            env=env,
            max_msg_delivery_time=max_msg_delivery_time,
        )
        self.stability_threshold = stability_threshold

        self.num_rounds_stationary = 0

    def __repr__(self):
        return f"DisclosureAttack_wBaselineInspection_wStationaryRounds(stability_threshold= {self.stability_threshold})"

    def try_to_get_target_server_id_set(self) -> Optional[set[str]]:
        if self.num_sample_sets_collected < 10:
            return None

        for server_id in (
            set(self.server_id_to_weight_map.keys())
            | set(self.server_id_to_baseline_weight_map.keys())
        ):
            avg_weight_diff = self.server_id_weight_diff_map[server_id]
            weight_diff = (
                self.server_id_to_weight_map[server_id]
                - self.server_id_to_baseline_weight_map[server_id]
            )

            diff = weight_diff - avg_weight_diff
            self.server_id_weight_diff_map[server_id] += 0.9 * diff

            if abs(diff) > self.stability_threshold:
                self.num_rounds_stationary = 0

        self.num_rounds_stationary += 1
        log(
            DEBUG, "",
            server_id_to_weight_map=self.server_id_to_weight_map,
            server_id_to_baseline_weight_map=self.server_id_to_baseline_weight_map,
            server_id_weight_diff_map=self.server_id_weight_diff_map,
            num_rounds_stationary=self.num_rounds_stationary,
        )

        if self.num_rounds_stationary == 20:
            # Cluster the weight diffs
            data = [
                [server_id, avg_weight_diff]
                for server_id, avg_weight_diff in self.server_id_weight_diff_map.items()
            ]
            array = numpy.array([[row[1]] for row in data])
            centroids, labels, inertia = sklearn.cluster.k_means(array, 2)
            log(
                DEBUG, "",
                centroids=centroids,
                labels=labels,
                inertia=inertia,
            )

            # Find `label_for_target_servers`
            centroid_and_label_list_sorted = sorted(
                [
                    (centroids[label].item(), label)
                    for label in range(2)
                ]
            )
            log(INFO, "", centroid_and_label_list_sorted=centroid_and_label_list_sorted)

            label_for_target_servers = centroid_and_label_list_sorted[1][1]

            # Return the set of target server ids
            return set(
                data[i][0]
                for i in range(len(data))
                if labels[i] == label_for_target_servers
            )

        return None


class DisclosureAttack_wBayesianEstimate(DisclosureAttack_wBaselineInspection):
    def __init__(
        self,
        env: simpy.Environment,
        max_msg_delivery_time: float,
        max_stdev: float,
        detection_threshold: float,
    ):
        self.server_id_to_num_times_in_sample_set_map = collections.defaultdict(int)
        self.server_id_to_num_in_baseline_sample_set_map = collections.defaultdict(int)

        super().__init__(
            env=env,
            max_msg_delivery_time=max_msg_delivery_time,
        )
        self.max_stdev = max_stdev
        self.detection_threshold = detection_threshold

    def __repr__(self):
        return "DisclosureAttack_wBayesianEstimate"

    def get_end_of_attack_log(self) -> dict:
        return {
            "max_stdev": self.max_stdev,
            "detection_threshold": self.detection_threshold,
            "server_id_to_freq_in_sample_set_map": {
                server_id: p_rv.mean()
                for server_id, p_rv in self.get_server_id_to_p_rv_map().items()
            },
            "server_id_to_freq_in_baseline_sample_set_map": {
                server_id: p_rv.mean()
                for server_id, p_rv in self.get_server_id_to_p_baseline_rv_map().items()
            },
        }

    def update(self, sample_candidate_set: set[str]):
        slog(
            DEBUG, self.env, self,
            "started",
            sample_candidate_set=sample_candidate_set,
        )

        for server_id in sample_candidate_set:
            self.server_id_to_num_times_in_sample_set_map[server_id] += 1

        self.num_sample_sets_collected += 1
        log(
            INFO, "updated",
            num_sample_sets_collected=self.num_sample_sets_collected,
            len_sample_candidate_set=len(sample_candidate_set),
            # sample_candidate_set=sample_candidate_set,
        )

    def baseline_inspection(self):
        interval_rv = random_variable.Exponential(mu=3 / self.max_msg_delivery_time)

        num_msgs_recved_for_get_request = 1
        while True:
            interval = interval_rv.sample()
            slog(DEBUG, self.env, self, "waiting", interval=interval)
            yield self.env.timeout(interval)

            sample_candidate_set = self.get_sample_candidate_set(
                num_msgs_recved_for_get_request=num_msgs_recved_for_get_request,
            )
            if not sample_candidate_set:
                slog(DEBUG, self.env, self, "skipping empty sample_candidate_set")
                continue

            for server_id in sample_candidate_set:
                self.server_id_to_num_in_baseline_sample_set_map[server_id] += 1

            slog(
                DEBUG, self.env, self,
                "baseline inspection round",
                # num_msgs_recved_for_get_request=num_msgs_recved_for_get_request,
                # sample_candidate_set=sample_candidate_set,
                num_baseline_sample_sets_collected=self.num_baseline_sample_sets_collected,
                # server_id_to_num_in_baseline_sample_set_map=self.server_id_to_num_in_baseline_sample_set_map,
            )
            self.num_baseline_sample_sets_collected += 1

    def get_server_id_to_p_rv_map(self) -> dict[str, random_variable.RandomVariable]:
        log(
            DEBUG, "",
            server_id_to_num_times_in_sample_set_map=self.server_id_to_num_times_in_sample_set_map,
            num_sample_sets_collected=self.num_sample_sets_collected,
        )

        # Note: `+ 1` is necessary to avoid getting nan values from Beta.stdev().
        return {
            server_id: random_variable.Beta(
                a=num_times_in_sample_set + 1,
                b=self.num_sample_sets_collected - num_times_in_sample_set + 1
            )
            for server_id, num_times_in_sample_set in self.server_id_to_num_times_in_sample_set_map.items()
        }

    def get_server_id_to_p_baseline_rv_map(self) -> dict[str, random_variable.RandomVariable]:
        log(
            DEBUG, "",
            server_id_to_num_in_baseline_sample_set_map=self.server_id_to_num_in_baseline_sample_set_map,
            num_baseline_sample_sets_collected=self.num_baseline_sample_sets_collected,
        )

        return {
            server_id: random_variable.Beta(
                a=num_times_in_sample_set + 1,
                b=self.num_baseline_sample_sets_collected - num_times_in_sample_set + 1
            )
            for server_id, num_times_in_sample_set in self.server_id_to_num_in_baseline_sample_set_map.items()
        }

    def is_attack_completed(self) -> bool:
        server_id_to_p_rv_map = self.get_server_id_to_p_rv_map()
        server_id_to_p_baseline_rv_map = self.get_server_id_to_p_baseline_rv_map()
        log(
            INFO, "",
            # server_id_to_p_rv_map=server_id_to_p_rv_map,
            # server_id_to_p_baseline_rv_map=server_id_to_p_baseline_rv_map,
            avg_p_rv_mean=self.get_avg_p_rv_mean(),
            avg_p_baseline_rv_mean=self.get_avg_p_baseline_rv_mean(),
        )

        for server_id in (
            set(server_id_to_p_rv_map.keys())
            | set(server_id_to_p_baseline_rv_map.keys())
        ):
            stdev = server_id_to_p_rv_map[server_id].stdev() if server_id in server_id_to_p_rv_map else float("Inf")
            stdev_baseline = server_id_to_p_baseline_rv_map[server_id].stdev() if server_id in server_id_to_p_baseline_rv_map else float("Inf")

            if (
                stdev is None or numpy.isnan(stdev)
                or stdev_baseline is None or numpy.isnan(stdev_baseline)
                or stdev > self.max_stdev
                or stdev_baseline > self.max_stdev
            ):
                log(
                    INFO, f"> server_id= {server_id}",
                    stdev=stdev,
                    stdev_baseline=stdev_baseline,
                    max_stdev=self.max_stdev,
                )
                return False

        return True

    def try_to_get_target_server_id_set(self) -> Optional[set[str]]:
        if (
            self.num_sample_sets_collected < 10
            or not self.is_attack_completed()
        ):
            return None

        return self.get_target_server_id_set()

    def get_target_server_id_set(self) -> set[str]:
        server_id_to_signal_map = self.get_server_id_to_signal_map()

        # Cluster the signals
        data = [
            [server_id, abs(signal)]
            for server_id, signal in server_id_to_signal_map.items()
        ]
        array = numpy.array([[row[1]] for row in data])
        centroids, labels, inertia = sklearn.cluster.k_means(array, 2)
        log(
            DEBUG, "",
            centroids=centroids,
            labels=labels,
            inertia=inertia,
        )

        # Find `label_for_target_servers`
        centroid_and_label_list_sorted = sorted(
            [
                (centroids[label].item(), label)
                for label in range(2)
            ]
        )
        log(INFO, "", centroid_and_label_list_sorted=centroid_and_label_list_sorted)

        label_for_target_servers = centroid_and_label_list_sorted[1][1]

        # Return the set of target server ids
        return set(
            data[i][0]
            for i in range(len(data))
            if labels[i] == label_for_target_servers
        )

    def get_server_id_to_signal_map(self) -> dict[str, float]:
        server_id_to_p_rv_map = self.get_server_id_to_p_rv_map()
        server_id_to_p_baseline_rv_map = self.get_server_id_to_p_baseline_rv_map()

        return {
            server_id: p_rv.mean() - server_id_to_p_baseline_rv_map[server_id].mean()
            for server_id, p_rv in server_id_to_p_rv_map.items()
        }

    def get_avg_p_rv_mean(self) -> float:
        return numpy.mean(
            [
                p_rv.mean()
                for p_rv in self.get_server_id_to_p_rv_map().values()
            ]
        )

    def get_avg_p_baseline_rv_mean(self) -> float:
        return numpy.mean(
            [
                p_rv.mean()
                for p_rv in self.get_server_id_to_p_baseline_rv_map().values()
            ]
        )


class DisclosureAttack_wOutlierDetection(DisclosureAttack_wBayesianEstimate):
    def __init__(
        self,
        env: simpy.Environment,
        max_msg_delivery_time: float,
        max_stdev: float,
        detection_threshold: float,
    ):
        super().__init__(
            env=env,
            max_msg_delivery_time=max_msg_delivery_time,
            max_stdev=max_stdev,
            detection_threshold=detection_threshold,
        )

    def __repr__(self):
        return "DisclosureAttack_wOutlierDetection"

    def get_target_server_id_set(self) -> set[str]:
        server_id_to_signal_map = self.get_server_id_to_signal_map()
        return [
            server_id
            for server_id, signal in server_id_to_signal_map.items()
            if signal >= self.detection_threshold
        ]


class DisclosureAttack_wOutlierDetection_wEarlyTermination(DisclosureAttack_wOutlierDetection):
    def __init__(
        self,
        env: simpy.Environment,
        max_msg_delivery_time: float,
        max_stdev: float,
        detection_threshold: float,
        num_servers_to_exclude_from_threshold: int,
    ):
        super().__init__(
            env=env,
            max_msg_delivery_time=max_msg_delivery_time,
            max_stdev=max_stdev,
            detection_threshold=detection_threshold,
        )
        self.num_servers_to_exclude_from_threshold = num_servers_to_exclude_from_threshold

    def __repr__(self):
        return "DisclosureAttack_wOutlierDetection_wEarlyTermination"

    def is_attack_completed(self) -> bool:
        server_id_to_p_rv_map = self.get_server_id_to_p_rv_map()
        server_id_to_p_baseline_rv_map = self.get_server_id_to_p_baseline_rv_map()
        log(
            INFO, "",
            # server_id_to_p_rv_map=server_id_to_p_rv_map,
            # server_id_to_p_baseline_rv_map=server_id_to_p_baseline_rv_map,
            avg_p_rv_mean=self.get_avg_p_rv_mean(),
            avg_p_baseline_rv_mean=self.get_avg_p_baseline_rv_mean(),
        )

        num_servers_w_large_stdev = 0
        for server_id in (
            set(server_id_to_p_rv_map.keys())
            | set(server_id_to_p_baseline_rv_map.keys())
        ):
            stdev = server_id_to_p_rv_map[server_id].stdev() if server_id in server_id_to_p_rv_map else float("Inf")
            stdev_baseline = server_id_to_p_baseline_rv_map[server_id].stdev() if server_id in server_id_to_p_baseline_rv_map else float("Inf")

            if (
                stdev is None or numpy.isnan(stdev)
                or stdev_baseline is None or numpy.isnan(stdev_baseline)
                or stdev > self.max_stdev
                or stdev_baseline > self.max_stdev
            ):
                log(
                    DEBUG, f"> server_id= {server_id}",
                    stdev=stdev,
                    stdev_baseline=stdev_baseline,
                    max_stdev=self.max_stdev,
                )
                num_servers_w_large_stdev += 1

            if num_servers_w_large_stdev > self.num_servers_to_exclude_from_threshold:
                return False

        return True


@dataclasses.dataclass
class ClassificationResult:
    num_targets_identified_as_target: int
    num_targets_identified_as_non_target: int
    num_non_targets_identified_as_target: int
    num_non_targets_identified_as_non_target: int

    prob_target_identified_as_non_target: float = dataclasses.field(init=False)
    prob_non_target_identified_as_target: float = dataclasses.field(init=False)

    def __post_init__(self):
        self.prob_target_identified_as_non_target = (
            self.num_targets_identified_as_non_target
            / (self.num_targets_identified_as_target + self.num_targets_identified_as_non_target)
        )

        self.prob_non_target_identified_as_target = (
            self.num_non_targets_identified_as_target
            / (self.num_non_targets_identified_as_target + self.num_non_targets_identified_as_non_target)
        )


@dataclasses.dataclass
class DisclosureAttackResult:
    time_to_deanonymize_list: list[float]
    num_rounds_list: list[int]
    target_server_set_accuracy: float
    classification_result_list: list[ClassificationResult]


@dataclasses.dataclass
class DisclosureAttackResult_wSignalSampleStrength(DisclosureAttackResult):
    signal_strength_for_target_server_list: list[float]
    signal_strength_for_non_target_server_list: list[float]
