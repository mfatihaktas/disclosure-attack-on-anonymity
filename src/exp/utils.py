import numpy

from typing import Callable

from src.debug_utils import log, DEBUG, INFO


def get_results_to_plot(
    x_list: list,
    disclosure_attack_result_given_x_func: Callable,
):
    log(
        INFO, "Started",
        x_list=x_list,
    )

    E_time_to_deanonymize_list = []
    std_time_to_deanonymize_list = []
    E_num_rounds_list = []
    std_num_rounds_list = []
    E_prob_non_target_identified_as_target_list = []
    std_prob_non_target_identified_as_target_list = []
    E_prob_target_identified_as_non_target_list = []
    std_prob_target_identified_as_non_target_list = []
    for x in x_list:
        log(INFO, f">> x= {x}")

        disclosure_attack_result = disclosure_attack_result_given_x_func(x)
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

        log(
            INFO, "",
            E_time_to_deanonymize=E_time_to_deanonymize,
            std_time_to_deanonymize=std_time_to_deanonymize,
            E_num_rounds=E_num_rounds,
            std_num_rounds=std_num_rounds,
            E_prob_non_target_identified_as_target=E_prob_non_target_identified_as_target,
            std_prob_non_target_identified_as_target=std_prob_non_target_identified_as_target,
            target_server_set_accuracy=disclosure_attack_result.target_server_set_accuracy,
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
