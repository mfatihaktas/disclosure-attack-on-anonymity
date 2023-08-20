import numpy

from src.prob import random_variable
from src.sim import tor as tor_module

from src.debug_utils import log, INFO
from src.plot_utils import NICE_BLUE, plot


def test_plot_avg_time_to_deanonymize_vs_num_servers():
    network_delay_rv = random_variable.Uniform(min_value=1, max_value=5)
    # idle_time_rv = random_variable.Exponential(mu=1)
    idle_time_rv = random_variable.Uniform(min_value=1, max_value=20)
    num_msgs_to_recv_for_get_request_rv = random_variable.DiscreteUniform(min_value=1, max_value=1)
    num_target_servers = 1
    error_percent = 0.05
    num_samples = 5

    log(INFO, "Started",
        network_delay_rv=network_delay_rv,
        idle_time_rv=idle_time_rv,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        num_target_servers=num_target_servers,
        error_percent=error_percent,
        num_samples=num_samples,
    )

    num_servers_list = []
    E_time_to_deanonymize_list = []
    for num_servers in range(2, 7):
        log(INFO, f">> num_servers= {num_servers}")
        num_clients = num_servers

        time_to_deanonymize_list = tor_module.sim_time_to_deanonymize_w_disclosure_attack(
            num_clients=num_clients,
            num_servers=num_servers,
            network_delay_rv=network_delay_rv,
            idle_time_rv=idle_time_rv,
            num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            num_target_servers=num_target_servers,
            error_percent=error_percent,
            num_samples=num_samples,
        )

        E_time_to_deanonymize = numpy.mean(time_to_deanonymize_list)
        log(INFO, "",
            E_time_to_deanonymize=E_time_to_deanonymize,
        )

        num_servers_list.append(num_servers)
        E_time_to_deanonymize_list.append(E_time_to_deanonymize)

    plot.plot(num_servers_list, E_time_to_deanonymize_list, color=NICE_BLUE, marker="x")

    # TODO: Add stdev with error margin bars.

    fontsize = 14
    plot.xlabel(r"$N_{\mathrm{server}}$", fontsize=fontsize)
    plot.ylabel(r"$E[T_{\mathrm{deanon}}]$", fontsize=fontsize)
    title = \
        r"$N_{\mathrm{client}} =$" + fr"${num_clients}$, " + \
        r"$T_{\mathrm{net}} \sim$" + fr"${network_delay_rv.to_latex()}$, " + \
        r"$T_{\mathrm{idle}} \sim$" + fr"${idle_time_rv.to_latex()}$, " + \
        r"$N_{\mathrm{get}} \sim$" + fr"${num_msgs_to_recv_for_get_request_rv.to_latex()}$, " + \
        r"$N_{\mathrm{target-server}} =$" + fr"${num_target_servers}$" + "\n" \
        r"$N_{\mathbf{samples}} =$" + fr"${num_samples}$"
    plot.title(title, fontsize=fontsize)  # , y=1.05
    plot.gcf().set_size_inches(6, 6)
    plot.savefig("plots/plot_avg_time_to_deanonymize_vs_num_servers.png", bbox_inches="tight")
    plot.gcf().clear()
    log(INFO, "Done.")
