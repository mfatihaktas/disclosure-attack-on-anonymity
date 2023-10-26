import joblib
import random
import simpy

from src import utils
from src.attack import (
    adversary as adversary_module,
    disclosure_attack,
)
from src.debug_utils import check, DEBUG, ERROR, INFO, log
from src.sim import message


class TorModel_wRounds:
    def __init__(
        self,
        env: simpy.Environment,
        num_clients: int,
        num_servers: int,
        num_target_servers: int,
        max_msg_delivery_time: float,
        prob_server_active: float,
        prob_attack_round: float,
    ):
        check(num_target_servers <= num_servers, "")

        self.env = env
        self.num_clients = num_clients
        self.num_servers = num_servers
        self.num_target_servers = num_target_servers
        self.max_msg_delivery_time = max_msg_delivery_time
        self.prob_server_active = prob_server_active
        self.prob_attack_round = prob_attack_round

        self.generate_model_events_process = env.process(self.generate_model_events())

    def __repr__(self):
        return (
            "TorModel_wRounds( \n"
            f"\t num_clients= {self.num_clients} \n"
            f"\t num_servers= {self.num_servers} \n"
            f"\t num_target_servers= {self.num_target_servers} \n"
            f"\t max_msg_delivery_time= {self.max_msg_delivery_time} \n"
            f"\t prob_server_active= {self.prob_server_active} \n"
            f"\t prob_attack_round= {self.prob_attack_round} \n"
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
            server_id_set = {
                utils.get_server_id(server_rank)
                for server_rank in range(self.num_servers)
                if random.random() <= self.prob_server_active
            }

            # Generate "server received" events.
            for server_id in server_id_set:
                msg = message.Message(
                    _id=f"{msg_count}",
                    _type=None,
                    src_id=server_id,
                    dst_id=target_client_id,
                )
                self.adversary.server_sent_msg(msg=msg)

            yield self.env.timeout(0.1 * self.max_msg_delivery_time)

            # Generate "client completed request" event.
            if random.random() <= self.prob_attack_round:
                target_server_id = utils.get_server_id(
                    random.randint(0, self.num_target_servers - 1)
                )
                msg = message.Message(
                    _id=f"{msg_count}",
                    _type=None,
                    src_id=target_server_id,
                    dst_id=target_client_id,
                )
                self.adversary.server_sent_msg(msg=msg)

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


def sim_w_disclosure_attack_w_joblib(
    num_clients: int,
    num_servers: int,
    num_target_servers: int,
    prob_server_active: float,
    prob_attack_round: float,
    num_samples: int,
    **kwargs,
) -> disclosure_attack.DisclosureAttackResult:
    max_msg_delivery_time = 1

    def sim():
        env = simpy.Environment()

        if "stability_threshold" in kwargs:
            adversary = disclosure_attack.DisclosureAttack_wBaselineInspection_wStationaryRounds(
                env=env,
                max_msg_delivery_time=max_msg_delivery_time,
                stability_threshold=kwargs["stability_threshold"],
            )
        elif "max_stdev" in kwargs:
            adversary = disclosure_attack.DisclosureAttack_wOutlierDetection(
                env=env,
                max_msg_delivery_time=max_msg_delivery_time,
                max_stdev=kwargs["max_stdev"],
            )
        else:
            log(ERROR, "", kwargs=kwargs)
            raise ValueError("Unexpected kwargs")

        tor = TorModel_wRounds(
            env=env,
            num_clients=num_clients,
            num_servers=num_servers,
            num_target_servers=num_target_servers,
            max_msg_delivery_time=max_msg_delivery_time,
            prob_server_active=prob_server_active,
            prob_attack_round=prob_attack_round,
        )

        tor.register_adversary(adversary=adversary)
        tor.run()

        result_list = [
            tor.get_target_server_ids(),
            tor.get_attack_completion_time(),
            tor.get_num_rounds(),
        ]
        if isinstance(adversary, disclosure_attack.DisclosureAttack_wBayesianEstimate):
            result_list.append(adversary.get_server_id_to_signal_map())

        return result_list

    true_target_server_id_set = set(
        f"{utils.get_server_id(server_rank)}" for server_rank in range(num_target_servers)
    )
    # log(WARNING, "", true_target_server_id_set=true_target_server_id_set)

    sim_result_list = joblib.Parallel(n_jobs=-1, prefer="threads")(
        [
            joblib.delayed(sim)()
            for _ in range(num_samples)
        ]
    )

    time_to_deanonymize_list = []
    num_rounds_list = []
    num_correct_target_server_sets = 0
    classification_result_list = []
    for sim_result in sim_result_list:
        target_server_id_set = sim_result[0]
        time_to_deanonymize = sim_result[1]
        num_rounds = sim_result[2]
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

    target_server_set_accuracy = num_correct_target_server_sets / num_samples
    if "stability_threshold" in kwargs:
        return disclosure_attack.DisclosureAttackResult(
            time_to_deanonymize_list=time_to_deanonymize_list,
            num_rounds_list=num_rounds_list,
            target_server_set_accuracy=target_server_set_accuracy,
            classification_result_list=classification_result_list,
        )

    elif "max_stdev" in kwargs:
        signal_strength_for_target_server_list = []
        signal_strength_for_non_target_server_list = []
        for sim_result in sim_result_list:
            server_id_to_signal_map = sim_result[3]
            log(INFO, "", server_id_to_signal_map=server_id_to_signal_map)

            signal_strength_for_target_server_list.extend(
                [
                    server_id_to_signal_map[utils.get_server_id(server_rank)]
                    for server_rank in range(num_target_servers)
                ]
            )
            signal_strength_for_non_target_server_list.extend(
                [
                    server_id_to_signal_map[utils.get_server_id(server_rank)]
                    for server_rank in range(num_target_servers, num_servers)
                ]
            )

        return disclosure_attack.DisclosureAttackResult_wSignalSampleStrength(
            time_to_deanonymize_list=time_to_deanonymize_list,
            num_rounds_list=num_rounds_list,
            target_server_set_accuracy=target_server_set_accuracy,
            classification_result_list=classification_result_list,
            signal_strength_for_target_server_list=signal_strength_for_target_server_list,
            signal_strength_for_non_target_server_list=signal_strength_for_non_target_server_list,
        )
