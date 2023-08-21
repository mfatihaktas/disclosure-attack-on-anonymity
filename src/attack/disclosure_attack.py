import bisect
import collections
import simpy

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

        self.target_server_ids = None
        self.time_to_complete_attack = None

    def __repr__(self):
        return f"DisclosureAttack(error_percent= {self.error_percent})"

    def client_sent_msg(self, msg: message.Message):
        pass

    def server_recved_msg(self, msg: message.Message):
        pass

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
        # log(INFO, "updated",
        #     num_sample_sets_collected=self.num_sample_sets_collected,
        #     sample_candidate_set=sample_candidate_set,
        # )

    def _check_for_completion(self) -> list[str] | None:
        if self.num_sample_sets_collected < 10:
            return None

        weight_and_server_id_list = sorted(
            [
                (weight, server_id)
                for server_id, weight in self.server_id_to_weight_map.items()
            ],
            reverse=True,
        )
        log(DEBUG, "", weight_and_server_id_list=weight_and_server_id_list)

        for m in range(1, len(weight_and_server_id_list) + 1):
            target_weight = 1 / m
            if all(
                abs(
                    weight_and_server_id_list[i][0] - target_weight
                ) / target_weight <= self.error_percent
                for i in range(m)
            ):
                return [
                    server_id
                    for (_, server_id) in weight_and_server_id_list[:m]
                ]

        return None

    def check_if_attack_completed(self) -> set[str] | None:
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

    def client_completed_get_request(
        self,
        num_msgs_recved_for_get_request: int,
    ):
        slog(
            DEBUG, self.env, self,
            "client completed request",
            num_msgs_recved_for_get_request=num_msgs_recved_for_get_request,
            server_id_to_time_epochs_msg_sent_map=self.server_id_to_time_epochs_msg_sent_map,
        )

        sample_candidate_set = self.get_sample_candidate_set(
            num_msgs_recved_for_get_request=num_msgs_recved_for_get_request,
        )
        check(sample_candidate_set, "`sample_candidate_set` cannot be empty")

        self.trim_server_id_to_time_epochs_msg_sent_map()

        # Update the attack state
        self.update(sample_candidate_set=sample_candidate_set)

        # Check if the attack is completed
        self.target_server_ids = self.check_if_attack_completed()
        if self.target_server_ids is not None:
            slog(
                INFO, self.env, self,
                "completed attack",
                target_server_ids=self.target_server_ids,
                server_id_to_weight_map=self.server_id_to_weight_map,
            )
            self.time_to_complete_attack = self.env.now
            self.attack_completed_event.succeed()

    def server_sent_msg(self, msg: message.Message):
        slog(DEBUG, self.env, self, "server sent msg")

        server_id = msg.src_id
        bisect.insort_left(
            self.server_id_to_time_epochs_msg_sent_map[server_id],
            self.env.now
        )


class DisclosureAttack_wBaselineInspection(DisclosureAttack):
    def __init__(
        self,
        env: simpy.Environment,
        max_msg_delivery_time: float,
        error_percent: float,
    ):
        super().__init__(
            env=env,
            max_msg_delivery_time=max_msg_delivery_time,
            error_percent=error_percent,
        )

        self.server_id_to_weight_map_for_baseline_inspection = collections.defaultdict(float)
        self.baseline_inspection_process = env.process(self.baseline_inspection())

    def __repr__(self):
        return f"DisclosureAttack_wBaselineInspection(error_percent= {self.error_percent})"

    def baseline_inspection(self):
        interval_rv = random_variable.Exponential(mu=1)

        num_msgs_recved_for_get_request = 1
        num_sample_sets_collected = 0
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
                set(self.server_id_to_weight_map_for_baseline_inspection.keys())
                | sample_candidate_set
            ):
                weight = self.server_id_to_weight_map_for_baseline_inspection[server_id]
                self.server_id_to_weight_map_for_baseline_inspection[server_id] = (
                    (
                        weight * num_sample_sets_collected
                        + int(server_id in sample_candidate_set)
                    )
                    / (num_sample_sets_collected + 1)
                )

            slog(
                INFO, self.env, self,
                "baseline inspection round",
                num_msgs_recved_for_get_request=num_msgs_recved_for_get_request,
                sample_candidate_set=sample_candidate_set,
                num_sample_sets_collected=num_sample_sets_collected,
                server_id_to_weight_map_for_baseline_inspection=self.server_id_to_weight_map_for_baseline_inspection,
            )
            num_sample_sets_collected += 1

    def check_if_attack_completed(self) -> set[str] | None:
        if self.num_sample_sets_collected < 10:
            return None

        weight_and_server_id_list = sorted(
            [
                (
                    max(
                        weight - self.server_id_to_weight_map_for_baseline_inspection[server_id],
                        0
                    ),
                    server_id
                )
                for server_id, weight in self.server_id_to_weight_map.items()
            ],
        )
        log(INFO, "", weight_and_server_id_list=weight_and_server_id_list)

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
