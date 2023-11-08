import joblib
import simpy

from src import utils
from src.attack import (
    adversary as adversary_module,
    disclosure_attack,
)
from src.debug_utils import check, DEBUG, ERROR, INFO, log
from src.model import model_w_rounds
from src.prob import random_variable
from src.sim import (
    tor as tor_module,
    tor_model as tor_model_module,
)


def get_adversary(
    env: simpy.Environment,
    max_msg_delivery_time: float,
    **kwargs,
) -> adversary_module.Adversary:
    if "stability_threshold" in kwargs:
        return disclosure_attack.DisclosureAttack_wBaselineInspection_wStationaryRounds(
            env=env,
            max_msg_delivery_time=max_msg_delivery_time,
            stability_threshold=kwargs["stability_threshold"],
        )

    elif "max_stdev" in kwargs:
        return disclosure_attack.DisclosureAttack_wOutlierDetection(
            env=env,
            max_msg_delivery_time=max_msg_delivery_time,
            max_stdev=kwargs["max_stdev"],
        )

    elif "detection_gap_exp_factor" in kwargs:
        analytical_model = model_w_rounds.Model_wRounds(
            num_clients=kwargs["num_clients"],
            num_servers=kwargs["num_servers"],
            num_target_servers=kwargs["num_target_servers"],
            prob_server_active=kwargs["prob_server_active"],
            prob_attack_round=kwargs["prob_attack_round"],
        )
        detection_gap_exp_factor = kwargs["detection_gap_exp_factor"]
        return disclosure_attack.DisclosureAttack_wOutlierDetection(
            env=env,
            max_msg_delivery_time=max_msg_delivery_time,
            max_stdev=analytical_model.max_stdev_of_prob_estimates(
                detection_gap_exp_factor=detection_gap_exp_factor,
            ),
            detection_threshold=analytical_model.detection_threshold(
                detection_gap_exp_factor=detection_gap_exp_factor,
            ),
        )

    else:
        log(ERROR, "", kwargs=kwargs)
        raise ValueError("Unexpected kwargs")


def sim_tor(
    num_clients: int,
    num_servers: int,
    num_target_servers: int,
    network_delay_rv: random_variable.RandomVariable,
    idle_time_rv: random_variable.RandomVariable,
    idle_time_rv_for_target_client: random_variable.RandomVariable,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
    num_samples: int,
    **kwargs,
):
    max_msg_delivery_time = 1

    env = simpy.Environment()

    adversary = get_adversary(
        env=env,
        max_msg_delivery_time=max_msg_delivery_time,
        **kwargs,
    )

    tor = tor_module.TorSystem(
        env=env,
        num_clients=num_clients,
        num_servers=num_servers,
        num_target_servers=num_target_servers,
        network_delay_rv=network_delay_rv,
        idle_time_rv=idle_time_rv,
        idle_time_rv_for_target_client=idle_time_rv_for_target_client,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
    )

    tor.register_adversary(adversary=adversary)
    tor.run()

    # Return the result
    result_list = [
        tor.get_target_server_ids(),
        tor.get_attack_completion_time(),
        tor.get_num_rounds(),
    ]
    if isinstance(adversary, disclosure_attack.DisclosureAttack_wBayesianEstimate):
        result_list.append(adversary.get_server_id_to_signal_map())

    return result_list


def sim_tor_model(
    num_clients: int,
    num_servers: int,
    num_target_servers: int,
    prob_server_active: float,
    prob_attack_round: float,
    num_samples: int,
    **kwargs,
):
    max_msg_delivery_time = 1

    env = simpy.Environment()

    adversary = get_adversary(
        env=env,
        max_msg_delivery_time=max_msg_delivery_time,
        num_clients=num_clients,
        num_servers=num_servers,
        num_target_servers=num_target_servers,
        prob_server_active=prob_server_active,
        prob_attack_round=prob_attack_round,
        **kwargs,
    )

    tor_model = tor_model_module.TorModel_wRounds(
        env=env,
        num_clients=num_clients,
        num_servers=num_servers,
        num_target_servers=num_target_servers,
        max_msg_delivery_time=max_msg_delivery_time,
        prob_server_active=prob_server_active,
        prob_attack_round=prob_attack_round,
    )

    tor_model.register_adversary(adversary=adversary)
    tor_model.run()

    # Return the result
    result_list = [
        tor_model.get_target_server_ids(),
        tor_model.get_attack_completion_time(),
        tor_model.get_num_rounds(),
    ]
    if isinstance(adversary, disclosure_attack.DisclosureAttack_wBayesianEstimate):
        result_list.append(adversary.get_server_id_to_signal_map())

    return result_list


def sim_w_disclosure_attack_w_joblib(
    num_clients: int,
    num_servers: int,
    num_target_servers: int,
    num_samples: int,
    w_model: bool,
    network_delay_rv: random_variable.RandomVariable = None,
    idle_time_rv: random_variable.RandomVariable = None,
    idle_time_rv_for_target_client: random_variable.RandomVariable = None,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable = None,
    prob_server_active: bool = None,
    prob_attack_round: bool = None,
    **kwargs,
) -> disclosure_attack.DisclosureAttackResult:
    true_target_server_id_set = set(
        f"{utils.get_server_id(server_rank)}" for server_rank in range(num_target_servers)
    )

    if w_model:
        sim_result_list = joblib.Parallel(n_jobs=-1, prefer="threads")(
            [
                joblib.delayed(sim_tor_model)(
                    num_clients=num_clients,
                    num_servers=num_servers,
                    num_target_servers=num_target_servers,
                    prob_server_active=prob_server_active,
                    prob_attack_round=prob_attack_round,
                    num_samples=num_samples,
                    **kwargs,
                )
                for _ in range(num_samples)
            ]
        )

    else:
        sim_result_list = joblib.Parallel(n_jobs=-1, prefer="threads")(
            [
                joblib.delayed(sim_tor)(
                    num_clients=num_clients,
                    num_servers=num_servers,
                    network_delay_rv=network_delay_rv,
                    idle_time_rv=idle_time_rv,
                    idle_time_rv_for_target_client=idle_time_rv_for_target_client,
                    num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
                    num_target_servers=num_target_servers,
                    num_samples=num_samples,
                    **kwargs,
                )
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

    elif "max_stdev" in kwargs or "detection_gap_exp_factor" in kwargs:
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
