import numpy

from src.prob import random_variable
from src.sim import tor as tor_module

from src.debug_utils import log, INFO
from src.plot_utils import NICE_BLUE, plot


def test_plot_avg_time_to_deanonymize_vs_num_servers():
    network_delay_rv = random_variable.Uniform(min_value=1, max_value=5)
    # idle_time_rv = random_variable.Exponential(mu=1)
    idle_time_rv = random_variable.Uniform(min_value=0, max_value=1)
    num_msgs_to_recv_for_get_request_rv = random_variable.DiscreteUniform(min_value=1, max_value=1)
    num_target_servers = 2
    error_percent = 0.2
    num_samples = 5

    log(
        INFO, "Started",
        network_delay_rv=network_delay_rv,
        idle_time_rv=idle_time_rv,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        num_target_servers=num_target_servers,
        error_percent=error_percent,
        num_samples=num_samples,
    )

    num_servers_list = []
    E_time_to_deanonymize_list = []
    std_time_to_deanonymize_list = []
    E_num_rounds_list = []
    std_num_rounds_list = []
    for num_servers in range(2, 6):
        log(INFO, f">> num_servers= {num_servers}")
        num_clients = num_servers

        disclosure_attack_result = tor_module.sim_w_disclosure_attack(
            num_clients=num_clients,
            num_servers=num_servers,
            network_delay_rv=network_delay_rv,
            idle_time_rv=idle_time_rv,
            num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            num_target_servers=num_target_servers,
            error_percent=error_percent,
            num_samples=num_samples,
        )

        E_time_to_deanonymize = numpy.mean(disclosure_attack_result.time_to_deanonymize_list)
        std_time_to_deanonymize = numpy.std(disclosure_attack_result.time_to_deanonymize_list)
        E_num_rounds = numpy.mean(disclosure_attack_result.num_rounds_list)
        std_num_rounds = numpy.std(disclosure_attack_result.num_rounds_list)
        log(
            INFO, "",
            E_time_to_deanonymize=E_time_to_deanonymize,
            std_time_to_deanonymize=std_time_to_deanonymize,
            E_num_rounds=E_num_rounds,
            std_num_rounds=std_num_rounds,
            target_server_accuracy=disclosure_attack_result.target_server_accuracy,
        )

        num_servers_list.append(num_servers)

        E_time_to_deanonymize_list.append(E_time_to_deanonymize)
        std_time_to_deanonymize_list.append(std_time_to_deanonymize)
        E_num_rounds_list.append(E_num_rounds)
        std_num_rounds_list.append(std_num_rounds)

    log(
        INFO, "",
        num_servers_list=num_servers_list,
        E_time_to_deanonymize_list=E_time_to_deanonymize_list,
        std_time_to_deanonymize_list=std_time_to_deanonymize_list,
        E_num_rounds_list=E_num_rounds_list,
        std_num_rounds_list=std_num_rounds_list,
    )
    # plot.errorbar(num_servers_list, E_time_to_deanonymize_list, yerr=std_time_to_deanonymize_list, color=NICE_BLUE, marker="x")
    plot.errorbar(num_servers_list, E_num_rounds_list, yerr=std_num_rounds_list, color=NICE_BLUE, marker="x")

    fontsize = 14
    plot.xlabel(r"$N_{\mathrm{server}}$", fontsize=fontsize)
    # plot.ylabel(r"$T_{\mathrm{deanon}}$", fontsize=fontsize)
    plot.ylabel("Number of rounds", fontsize=fontsize)
    title = (
        r"$T_{\mathrm{net}} \sim$" + fr"${network_delay_rv.to_latex()}$, "
        r"$T_{\mathrm{idle}} \sim$" + fr"${idle_time_rv.to_latex()}$, "
        r"$N_{\mathrm{get}} \sim$" + fr"${num_msgs_to_recv_for_get_request_rv.to_latex()}$, " + "\n"
        r"$N_{\mathrm{target-server}} =$" + fr"${num_target_servers}$, "
        r"$N_{\mathrm{samples}} =$" + fr"${num_samples}$"
    )
    plot.title(title, fontsize=fontsize)
    plot.gcf().set_size_inches(6, 4)
    plot.savefig("plots/plot_time_to_deanon_vs_num_servers.png", bbox_inches="tight")
    plot.gcf().clear()
    log(INFO, "Done")
