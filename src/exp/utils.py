import numpy

from src.debug_utils import log, DEBUG, INFO

from src.model import model_w_rounds as model_w_rounds_module
from src.sim import tor_model as tor_model_module


def get_results_to_plot_w_model(
    num_target_servers: int,
    num_servers_list: list[int],
    prob_server_active: float,
    prob_attack_round: float,
    num_samples: int,
    **kwargs,
):
    log(
        INFO, "Started",
        num_target_servers=num_target_servers,
        num_servers_list=num_servers_list,
        prob_server_active=prob_server_active,
        prob_attack_round=prob_attack_round,
        num_samples=num_samples,
        kwargs=kwargs,
    )

    prob_server_i_receives_list = []
    prob_server_i_receives_given_attack_round_list = []

    E_time_to_deanonymize_list = []
    std_time_to_deanonymize_list = []
    E_num_rounds_list = []
    std_num_rounds_list = []
    E_prob_non_target_identified_as_target_list = []
    std_prob_non_target_identified_as_target_list = []
    E_prob_target_identified_as_non_target_list = []
    std_prob_target_identified_as_non_target_list = []
    for num_servers in num_servers_list:
        log(INFO, f">> num_servers= {num_servers}")
        num_clients = num_servers

        disclosure_attack_result = tor_model_module.sim_w_disclosure_attack_w_joblib(
            num_clients=num_clients,
            num_servers=num_servers,
            num_target_servers=num_target_servers,
            prob_server_active=prob_server_active,
            prob_attack_round=prob_attack_round,
            num_samples=num_samples,
            **kwargs,
        )
        log(INFO, "", disclosure_attack_result=disclosure_attack_result)

        # Sim
        E_time_to_deanonymize = numpy.mean(disclosure_attack_result.time_to_deanonymize_list)
        std_time_to_deanonymize = numpy.std(disclosure_attack_result.time_to_deanonymize_list)
        E_time_to_deanonymize_list.append(E_time_to_deanonymize)
        std_time_to_deanonymize_list.append(std_time_to_deanonymize)

        E_num_rounds = numpy.mean(disclosure_attack_result.num_rounds_list)
        std_num_rounds = numpy.std(disclosure_attack_result.num_rounds_list)
        E_num_rounds_list.append(E_num_rounds)
        std_num_rounds_list.append(std_num_rounds)

        prob_target_identified_as_non_target_list = [
            classification_result.prob_target_identified_as_non_target
            for classification_result in disclosure_attack_result.classification_result_list
        ]
        E_prob_target_identified_as_non_target = numpy.mean(prob_target_identified_as_non_target_list)
        std_prob_target_identified_as_non_target = numpy.std(prob_target_identified_as_non_target_list)
        E_prob_target_identified_as_non_target_list.append(E_prob_target_identified_as_non_target)
        std_prob_target_identified_as_non_target_list.append(std_prob_target_identified_as_non_target)

        prob_non_target_identified_as_target_list = [
            classification_result.prob_non_target_identified_as_target
            for classification_result in disclosure_attack_result.classification_result_list
        ]
        E_prob_non_target_identified_as_target = numpy.mean(prob_non_target_identified_as_target_list)
        std_prob_non_target_identified_as_target = numpy.std(prob_non_target_identified_as_target_list)
        E_prob_non_target_identified_as_target_list.append(E_prob_non_target_identified_as_target)
        std_prob_non_target_identified_as_target_list.append(std_prob_non_target_identified_as_target)

        # Model
        model_w_rounds = model_w_rounds_module.Model_wRounds(
            num_clients=num_clients,
            num_servers=num_servers,
            num_target_servers=num_target_servers,
            prob_server_active=prob_server_active,
            prob_attack_round=prob_attack_round,
        )
        prob_server_i_receives = model_w_rounds.prob_server_i_receives()
        prob_server_i_receives_list.append(prob_server_i_receives)
        prob_server_i_receives_given_attack_round = model_w_rounds.prob_server_i_receives_given_attack_round()
        prob_server_i_receives_given_attack_round_list.append(prob_server_i_receives_given_attack_round)

        log(
            INFO, "",
            E_time_to_deanonymize=E_time_to_deanonymize,
            std_time_to_deanonymize=std_time_to_deanonymize,
            E_num_rounds=E_num_rounds,
            std_num_rounds=std_num_rounds,
            E_prob_non_target_identified_as_target=E_prob_non_target_identified_as_target,
            std_prob_non_target_identified_as_target=std_prob_non_target_identified_as_target,
            target_server_set_accuracy=disclosure_attack_result.target_server_set_accuracy,
            prob_server_i_receives=prob_server_i_receives,
            prob_server_i_receives_given_attack_round=prob_server_i_receives_given_attack_round,
        )


    log(
        INFO, "",
        E_time_to_deanonymize_list=E_time_to_deanonymize_list,
        std_time_to_deanonymize_list=std_time_to_deanonymize_list,
        E_num_rounds_list=E_num_rounds_list,
        std_num_rounds_list=std_num_rounds_list,
        E_prob_target_identified_as_non_target_list=E_prob_target_identified_as_non_target_list,
        std_prob_target_identified_as_non_target_list=std_prob_target_identified_as_non_target_list,
        E_prob_non_target_identified_as_target_list=E_prob_non_target_identified_as_target_list,
        std_prob_non_target_identified_as_target_list=std_prob_non_target_identified_as_target_list,
        prob_server_i_receives_list=prob_server_i_receives_list,
        prob_server_i_receives_given_attack_round_list=prob_server_i_receives_given_attack_round_list,
    )

    return dict(
        E_time_to_deanonymize_list=E_time_to_deanonymize_list,
        std_time_to_deanonymize_list=std_time_to_deanonymize_list,
        E_num_rounds_list=E_num_rounds_list,
        std_num_rounds_list=std_num_rounds_list,
        E_prob_non_target_identified_as_target_list=E_prob_non_target_identified_as_target_list,
        std_prob_non_target_identified_as_target_list=std_prob_non_target_identified_as_target_list,
        E_prob_target_identified_as_non_target_list=E_prob_target_identified_as_non_target_list,
        std_prob_target_identified_as_non_target_list=std_prob_target_identified_as_non_target_list,
    )
