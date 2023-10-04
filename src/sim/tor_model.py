import random
import simpy

from src.attack import (
    adversary as adversary_module,
    disclosure_attack,
)
from src.debug_utils import check, DEBUG, INFO, log
from src.sim import message


class TorModel():
    def __init__(
        self,
        env: simpy.Environment,
        num_clients: int,
        num_servers: int,
        num_target_servers: int,
        max_msg_delivery_time: float,
        prob_target_server_recv: float,
        prob_non_target_server_recv: float,
    ):
        check(num_target_servers <= num_servers, "")

        self.env = env
        self.num_clients = num_clients
        self.num_servers = num_servers
        self.num_target_servers = num_target_servers
        self.max_msg_delivery_time = max_msg_delivery_time
        self.prob_target_server_recv = prob_target_server_recv
        self.prob_non_target_server_recv = prob_non_target_server_recv

        self.generate_model_events_process = env.process(self.generate_model_events())

    def __repr__(self):
        return (
            "TorModel( \n"
            f"\t num_clients= {self.num_clients} \n"
            f"\t num_servers= {self.num_servers} \n"
            f"\t num_target_servers= {self.num_target_servers} \n"
            f"\t max_msg_delivery_time= {self.max_msg_delivery_time} \n"
            f"\t prob_target_server_recv= {self.prob_target_server_recv} \n"
            f"\t prob_non_target_server_recv= {self.prob_non_target_server_recv} \n"
            ")"
        )

    def register_adversary(self, adversary: adversary_module.Adversary):
        self.adversary = adversary
        log(DEBUG, "Registered \n", adversary=adversary)

    def get_attack_completion_time(self) -> float:
        return self.adversary.time_to_complete_attack

    def get_num_rounds(self) -> int:
        return self.adversary.num_sample_sets_collected

    def get_target_server_ids(self) -> set[str]:
        return self.adversary.target_server_id_set

    def generate_model_events(self):
        log(DEBUG, "Started")

        target_client_id = -1
        msg_count = 0
        while True:
            # Pick the servers that will receive a message.
            server_id_list = []
            for server_rank in range(self.num_servers):
                p = (
                    self.prob_target_server_recv
                    if server_rank < self.num_target_servers else
                    self.prob_non_target_server_recv
                )
                if random.random() <= p:
                    server_id_list.append(f"s{server_rank}")

            # Generate "server received" events.
            for server_id in server_id_list:
                msg = message.Message(
                    _id=f"{msg_count}",
                    _type=None,
                    src_id=server_id,
                    dst_id=target_client_id,
                )
                self.adversary.server_sent_msg(msg=msg)

            # Generate "client completed request" event.
            yield self.env.timeout(0.1 * self.max_msg_delivery_time)

            self.adversary.client_completed_get_request(
                num_msgs_recved_for_get_request=1,
            )

            # Wait long enough for the next round.
            yield self.env.timeout(2 * self.max_msg_delivery_time)

        log(DEBUG, "Done")

    def run(self):
        log(DEBUG, "Started")
        self.env.run(until=self.adversary.attack_completed_event)
        log(DEBUG, "Done")


def sim_w_disclosure_attack(
    num_clients: int,
    num_servers: int,
    num_target_servers: int,
    prob_target_server_recv: float,
    prob_non_target_server_recv: float,
    diff_threshold: float,
    num_samples: int,
) -> disclosure_attack.DisclosureAttackResult:
    max_msg_delivery_time = 1

    def sim():
        env = simpy.Environment()

        # adversary = disclosure_attack.DisclosureAttack(
        adversary = disclosure_attack.DisclosureAttack_wBaselineInspection(
            env=env,
            max_msg_delivery_time=max_msg_delivery_time,
            diff_threshold=diff_threshold,
        )

        tor = TorModel(
            env=env,
            num_clients=num_clients,
            num_servers=num_servers,
            num_target_servers=num_target_servers,
            max_msg_delivery_time=max_msg_delivery_time,
            prob_target_server_recv=prob_target_server_recv,
            prob_non_target_server_recv=prob_non_target_server_recv,
        )

        tor.register_adversary(adversary=adversary)
        tor.run()

        return (
            tor.get_target_server_ids(),
            tor.get_attack_completion_time(),
            tor.get_num_rounds()
        )

    true_target_server_id_set = set(
        f"s{server_id}" for server_id in range(num_target_servers)
    )
    # log(WARNING, "", true_target_server_id_set=true_target_server_id_set)

    time_to_deanonymize_list = []
    num_rounds_list = []
    num_correct_target_server_sets = 0
    classification_result_list = []
    for _ in range(num_samples):
        target_server_id_set, time_to_deanonymize, num_rounds = sim()
        log(
            INFO, "",
            target_server_id_set=target_server_id_set,
            time_to_deanonymize=time_to_deanonymize,
            num_rounds=num_rounds,
        )

        time_to_deanonymize_list.append(time_to_deanonymize)
        num_rounds_list.append(num_rounds)

        num_correct_target_server_sets += int(true_target_server_id_set == target_server_id_set)

        # Append `classification_result`
        num_targets_identified_as_target = 0
        num_non_targets_identified_as_target = 0
        for target_server_id in target_server_id_set:
            if target_server_id in true_target_server_id_set:
                num_targets_identified_as_target += 1
            else:
                num_non_targets_identified_as_target += 1

        classification_result = disclosure_attack.ClassificationResult(
            num_targets_identified_as_target=num_targets_identified_as_target,
            num_targets_identified_as_non_target=num_target_servers - num_targets_identified_as_target,
            num_non_targets_identified_as_target=num_non_targets_identified_as_target,
            num_non_targets_identified_as_non_target=num_servers - num_target_servers - num_non_targets_identified_as_target,
        )
        classification_result_list.append(classification_result)

    return disclosure_attack.DisclosureAttackResult(
        time_to_deanonymize_list=time_to_deanonymize_list,
        num_rounds_list=num_rounds_list,
        target_server_set_accuracy=num_correct_target_server_sets / num_samples,
        classification_result_list=classification_result_list,
    )
