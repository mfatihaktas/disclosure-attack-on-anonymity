import bisect
import collections
import simpy

from src.attack import adversary as adversary_module
from src.sim import message

from src.debug_utils import log, DEBUG, slog


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

    def update(self, sample_candidate_set: set[str]):
        for server_id in sample_candidate_set:
            cur_weight = self.server_id_to_weight_map[server_id]
            self.server_id_to_weight_map[server_id] = (
                (cur_weight * self.num_sample_sets_collected)
                / (self.num_sample_sets_collected + 1)
            )

        self.num_sample_sets_collected += 1
        log(DEBUG, "updated", num_sample_sets_collected=self.num_sample_sets_collected)

    def check_for_completion(self) -> list[str] | None:
        if self.num_sample_sets_collected < 10:
            return False

        weight_and_server_id_list = sorted(
            [
                (weight, server_id)
                for server_id, weight in self.server_id_to_weight_map.items()
            ]
        )

        for m in range(1, len(weight_and_server_id_list) + 1):
            target_weight = 1 / m
            if all(
                abs(
                    weight_and_server_id_list[i][0] - target_weight
                ) <= self.error_margin
                for i in range(m)
            ):
                return [
                    server_id
                    for _, server_id in weight_and_server_id_list[m]
                ]

        return None

    def client_completed_get_request(
        self,
        num_msgs_recved_for_get_request: int,
    ):
        slog(DEBUG, self.env, self,
             "client completed request",
             num_msgs_recved_for_get_request=num_msgs_recved_for_get_request,
        )

        min_time_epoch = self.env.now - self.max_msg_delivery_time
        sample_candidate_set = set()
        for server_id, time_epochs_msg_sent in self.server_id_to_time_epochs_msg_sent_map.items():
            if not time_epochs_msg_sent:
                continue

            first_index_smaller = bisect.bisect_left(time_epochs_msg_sent, min_time_epoch)
            if len(time_epochs_msg_sent) - first_index_smaller - 1 >= num_msgs_recved_for_get_request:
                sample_candidate_set.add(server_id)

        self.server_id_to_time_epochs_msg_sent_map.clear()

        # Update the attack state
        self.update(sample_candidate_set=sample_candidate_set)

        # Check if the attack is completed
        self.target_server_ids = self.check_for_completion()
        if self.target_server_ids is not None:
            self.attack_completed_event.succeed()

    def server_sent_msg(self, msg: message.Message):
        slog(DEBUG, self.env, self, "server sent msg")

        server_id = msg.src_id
        bisect.insort_left(
            self.server_id_to_time_epochs_msg_sent_map[server_id],
            self.env.now
        )
