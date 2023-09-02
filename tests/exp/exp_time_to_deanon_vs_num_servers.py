import numpy

from src.prob import random_variable
from src.sim import tor as tor_module

from src.debug_utils import log, INFO
from src.plot_utils import NICE_BLUE, NICE_ORANGE, NICE_RED, plot


def plot_avg_time_to_deanonymize_vs_num_servers(
    network_delay_rv: random_variable.RandomVariable,
    idle_time_rv: random_variable.RandomVariable,
    idle_time_rv_for_target_client: random_variable.RandomVariable,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
    num_target_servers: int,
    num_servers_list: list[int],
    diff_threshold: float,
    num_samples: int,
):
    log(
        INFO, "Started",
        network_delay_rv=network_delay_rv,
        idle_time_rv=idle_time_rv,
        idle_time_rv_for_target_client=idle_time_rv_for_target_client,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        num_target_servers=num_target_servers,
        num_servers_list=num_servers_list,
        diff_threshold=diff_threshold,
        num_samples=num_samples,
    )

    E_time_to_deanonymize_list = []
    std_time_to_deanonymize_list = []
    E_num_rounds_list = []
    std_num_rounds_list = []
    E_true_target_rate_list = []
    std_true_target_rate_list = []
    E_num_false_non_targets_list = []
    std_num_false_non_targets_list = []
    num_false_targets_tuple_list = []
    for num_servers in num_servers_list:
        log(INFO, f">> num_servers= {num_servers}")
        num_clients = num_servers

        disclosure_attack_result = tor_module.sim_w_disclosure_attack(
            num_clients=num_clients,
            num_servers=num_servers,
            network_delay_rv=network_delay_rv,
            idle_time_rv=idle_time_rv,
            idle_time_rv_for_target_client=idle_time_rv_for_target_client,
            num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            num_target_servers=num_target_servers,
            diff_threshold=diff_threshold,
            num_samples=num_samples,
        )

        E_time_to_deanonymize = numpy.mean(disclosure_attack_result.time_to_deanonymize_list)
        std_time_to_deanonymize = numpy.std(disclosure_attack_result.time_to_deanonymize_list)
        E_time_to_deanonymize_list.append(E_time_to_deanonymize)
        std_time_to_deanonymize_list.append(std_time_to_deanonymize)

        E_num_rounds = numpy.mean(disclosure_attack_result.num_rounds_list)
        std_num_rounds = numpy.std(disclosure_attack_result.num_rounds_list)
        E_num_rounds_list.append(E_num_rounds)
        std_num_rounds_list.append(std_num_rounds)

        true_target_rate_list = [
            classification_result.true_target_rate
            for classification_result in disclosure_attack_result.classification_result_list
        ]
        E_true_target_rate = numpy.mean(true_target_rate_list)
        std_true_target_rate = numpy.std(true_target_rate_list)
        E_true_target_rate_list.append(E_true_target_rate)
        std_true_target_rate_list.append(std_true_target_rate)

        num_false_non_targets_list = [
            classification_result.num_false_non_targets
            for classification_result in disclosure_attack_result.classification_result_list
        ]
        E_num_false_non_targets = numpy.mean(num_false_non_targets_list)
        std_num_false_non_targets = numpy.std(num_false_non_targets_list)
        E_num_false_non_targets_list.append(E_num_false_non_targets)
        std_num_false_non_targets_list.append(std_num_false_non_targets)

        num_false_targets_tuple_list.append(
            [
                classification_result.num_false_targets
                for classification_result in disclosure_attack_result.classification_result_list
            ]
        )

        log(
            INFO, "",
            E_time_to_deanonymize=E_time_to_deanonymize,
            std_time_to_deanonymize=std_time_to_deanonymize,
            E_num_rounds=E_num_rounds,
            std_num_rounds=std_num_rounds,
            E_true_target_rate=E_true_target_rate,
            std_true_target_rate=std_true_target_rate,
            E_num_false_non_targets=E_num_false_non_targets,
            std_num_false_non_targets=std_num_false_non_targets,
            target_server_set_accuracy=disclosure_attack_result.target_server_set_accuracy,
            num_false_targets_tuple_list=num_false_targets_tuple_list,
        )

    log(
        INFO, "",
        E_time_to_deanonymize_list=E_time_to_deanonymize_list,
        std_time_to_deanonymize_list=std_time_to_deanonymize_list,
        E_num_rounds_list=E_num_rounds_list,
        std_num_rounds_list=std_num_rounds_list,
        E_true_target_rate_list=E_true_target_rate_list,
        std_true_target_rate_list=std_true_target_rate_list,
        E_num_false_non_targets_list=E_num_false_non_targets_list,
        std_num_false_non_targets_list=std_num_false_non_targets_list,
    )

    # Plot
    fontsize = 14
    num_columns = 3
    fig, axs = plot.subplots(1, num_columns)

    ax = axs[0]
    plot.sca(ax)
    plot.errorbar(num_servers_list, E_num_rounds_list, yerr=std_num_rounds_list, color=NICE_BLUE, marker="o")
    plot.xlabel("Number of candidate servers", fontsize=fontsize)
    # plot.ylabel(r"$T_{\mathrm{deanon}}$", fontsize=fontsize)
    plot.ylabel("Number of rounds", fontsize=fontsize)

    ax = axs[1]
    plot.sca(ax)
    plot.errorbar(num_servers_list, E_true_target_rate_list, yerr=std_true_target_rate_list, color=NICE_RED, marker="o")
    plot.xlabel("Number of candidate servers", fontsize=fontsize)
    plot.ylabel("True target rate", fontsize=fontsize)

    ax = axs[2]
    plot.sca(ax)
    for num_servers, num_false_targets_tuple in zip(num_servers_list, num_false_targets_tuple_list):
        for num_false_targets in num_false_targets_tuple:
            plot.plot([num_servers], [num_false_targets], color=NICE_ORANGE, marker="x", mew=2, ms=5)
    plot.xlabel("Number of candidate servers", fontsize=fontsize)
    plot.ylabel("Number of false targets", fontsize=fontsize)

    title = (
        r"$T_{\mathrm{net}} \sim$" + fr"${network_delay_rv.to_latex()}$, "
        r"$T_{\mathrm{idle}} \sim$" + fr"${idle_time_rv.to_latex()}$, "
        r"$N_{\mathrm{get}} \sim$" + fr"${num_msgs_to_recv_for_get_request_rv.to_latex()}$, "  # + "\n"
        r"$N_{\mathrm{target}} =$" + fr"${num_target_servers}$, "
        r"$N_{\mathrm{samples}} =$" + fr"${num_samples}$"
    )
    plot.suptitle(title, fontsize=fontsize)

    fig.set_size_inches(num_columns * 6, 4)
    plot.subplots_adjust(hspace=0.25, wspace=0.25)

    plot_name = (
        "plot_time_to_deanon_vs_num_servers"
        f"_network_delay_rv_{network_delay_rv}"
        f"_idle_time_rv_{idle_time_rv}"
        f"_num_msgs_to_recv_for_get_request_rv_{num_msgs_to_recv_for_get_request_rv}"
        f"_num_target_servers_{num_target_servers}"
        f"_num_samples_{num_samples}"
    )
    plot.savefig(f"plots/{plot_name}.pdf", bbox_inches="tight")

    plot.gcf().clear()
    log(INFO, "Done")


if __name__ == "__main__":
    network_delay_rv = random_variable.Uniform(min_value=1, max_value=5)
    # idle_time_rv = random_variable.Exponential(mu=1)
    idle_time_rv = random_variable.Uniform(min_value=0, max_value=1)
    idle_time_rv_for_target_client = random_variable.Uniform(min_value=4, max_value=6)
    num_msgs_to_recv_for_get_request_rv = random_variable.DiscreteUniform(min_value=1, max_value=1)
    num_target_servers = 2
    num_servers_list = [3]
    # num_servers_list = list(range(3, 20))
    # num_servers_list = [3, 10, 20, 50, 100, 200]
    # num_servers_list = [3, 20, 50, 100, 200, 400]
    # num_servers_list = [3, 20, 50, 100, 200, 500, 1000, 1500, 2000, 2500, 3000]
    diff_threshold = 0.003
    num_samples = 2  # 5

    plot_avg_time_to_deanonymize_vs_num_servers(
        network_delay_rv=network_delay_rv,
        idle_time_rv=idle_time_rv,
        idle_time_rv_for_target_client=idle_time_rv_for_target_client,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        num_target_servers=num_target_servers,
        num_servers_list=num_servers_list,
        diff_threshold=diff_threshold,
        num_samples=num_samples,
    )
