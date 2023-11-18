from typing import Callable, Tuple

from src.exp import utils

from src.attack import disclosure_attack
from src.debug_utils import log, DEBUG, INFO
from src.plot_utils import NICE_BLUE, NICE_ORANGE, NICE_RED, plot
from src.prob import random_variable
from src.sim import sim as sim_module


def plot_(
    x_list: float,
    results_dict: dict[str, list[float]],
    x_label: str,
    title: str,
    plot_name: str,
):
    fontsize = 14
    num_columns = 3
    fig, axs = plot.subplots(1, num_columns)

    ax = axs[0]
    plot.sca(ax)
    plot.xlabel(x_label, fontsize=fontsize)
    plot.errorbar(x_list, results_dict["E_time_to_deanonymize_list"], yerr=results_dict["std_time_to_deanonymize_list"], color=NICE_BLUE, marker="o")
    plot.ylabel("Time-to-deanonymize", fontsize=fontsize)

    ax = axs[1]
    plot.sca(ax)
    plot.errorbar(x_list, results_dict["E_prob_target_identified_as_non_target_list"], yerr=results_dict["std_prob_target_identified_as_non_target_list"], color=NICE_ORANGE, marker="o")
    plot.xlabel(x_label, fontsize=fontsize)
    plot.ylabel(r"$\mathrm{Pr}\{$target identified as non-target$\}$", fontsize=fontsize)

    ax = axs[2]
    plot.sca(ax)
    plot.errorbar(x_list, results_dict["E_prob_non_target_identified_as_target_list"], yerr=results_dict["std_prob_non_target_identified_as_target_list"], color=NICE_RED, marker="o")
    plot.xlabel(x_label, fontsize=fontsize)
    plot.ylabel(r"$\mathrm{Pr}\{$non-target identified as target$\}$", fontsize=fontsize)

    st = plot.suptitle(title, fontsize=fontsize)  # , y=1.1

    fig.set_size_inches(num_columns * 6, 4)
    plot.subplots_adjust(hspace=0.25, wspace=0.25)

    plot.savefig(f"plots/{plot_name}.pdf", bbox_extra_artists=[st], bbox_inches="tight")
    plot.gcf().clear()


def plot_perf(
    x_list: list[float],
    disclosure_attack_result_given_x_func: Callable,
    x_label: str,
    title: str,
    plot_name: str,
):
    results_dict = utils.get_results_to_plot(
        x_list=x_list,
        disclosure_attack_result_given_x_func=disclosure_attack_result_given_x_func,
    )

    plot_(
        x_list=x_list,
        results_dict=results_dict,
        x_label=x_label,
        title=title,
        plot_name=plot_name,
    )


def get_title_and_plot_name_tail(
    w_model: bool,
    num_target_servers: int,
    num_samples: int,
    **kwargs,
) -> Tuple[str, str]:
    title = ""
    plot_name_tail = f"wmodel_{w_model}"

    if "num_servers" in kwargs:
        title += r"$N_{\mathrm{server}} =$" + fr"${kwargs['num_servers']}$, "
        plot_name_tail += f"_nservers_{kwargs['num_servers']}"
    title += r"$N_{\mathrm{target}} =$" + fr"${num_target_servers}$, "
    plot_name_tail += f"_ntarget_{num_target_servers}"

    if w_model:
        if "prob_server_active" in kwargs:
            title += r"$p_{\mathrm{server}} =$" + fr"${kwargs['prob_server_active']}$, "
            plot_name_tail += f"_pserver_{kwargs['prob_server_active']}"

        title += r"$p_{\mathrm{client}} =$" + fr"${kwargs['prob_attack_round']}$, "
        plot_name_tail += f"_pattackround_{kwargs['prob_attack_round']}"

    else:
        title += (
            r"$T_{\mathrm{net}} \sim$" + fr"${kwargs['network_delay_rv'].to_latex()}$, "
            r"$T_{\mathrm{idle}} \sim$" + fr"${kwargs['client_idle_time_rv'].to_latex()}$, "
            r"$N_{\mathrm{get}} \sim$" + fr"${kwargs['num_msgs_to_recv_for_get_request_rv'].to_latex()}$, "
        )
        plot_name_tail += (
            f"_net_delay_{kwargs['network_delay_rv']}"
            f"_idle_time_{kwargs['client_idle_time_rv']}"
            f"_num_msgs_to_recv_{kwargs['num_msgs_to_recv_for_get_request_rv']}"
        )

    if "max_stdev" in kwargs:
        title += r"$\sigma_{\mathrm{max}} =$" + fr"${kwargs['max_stdev']}$, "
        plot_name_tail += f"_max_stdev_{kwargs['max_stdev']}"
    if "detection_gap_exp_factor" in kwargs:
        title += fr"$\gamma = {kwargs['detection_gap_exp_factor']}$, "
        plot_name_tail += f"_detection_gap_exp_factor_{kwargs['detection_gap_exp_factor']}"

    title += r"$N_{\mathrm{samples}} =$" + fr"${num_samples}$"
    plot_name_tail += f"_nsamples_{num_samples}"

    return title, plot_name_tail


def plot_perf_vs_num_servers(
    num_servers_list: list[float],
    num_target_servers: int,
    num_samples: int,
    w_model: bool,
    network_delay_rv: random_variable.RandomVariable = None,
    client_idle_time_rv: random_variable.RandomVariable = None,
    target_client_idle_time_rv: random_variable.RandomVariable = None,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable = None,
    prob_server_active: float = None,
    prob_attack_round: float = None,
    **kwargs,
):
    def disclosure_attack_result_given_x_func(
        num_servers: int,
    ) -> disclosure_attack.DisclosureAttackResult:
        return sim_module.sim_w_disclosure_attack_w_joblib(
            num_clients=num_servers,
            num_servers=num_servers,
            num_target_servers=num_target_servers,
            num_samples=num_samples,
            w_model=w_model,
            network_delay_rv=network_delay_rv,
            client_idle_time_rv=client_idle_time_rv,
            target_client_idle_time_rv=target_client_idle_time_rv,
            num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            prob_server_active=prob_server_active,
            prob_attack_round=prob_attack_round,
            **kwargs,
        )

    title, plot_name_tail = get_title_and_plot_name_tail(
        w_model=w_model,
        num_target_servers=num_target_servers,
        num_samples=num_samples,
        network_delay_rv=network_delay_rv,
        client_idle_time_rv=client_idle_time_rv,
        target_client_idle_time_rv=target_client_idle_time_rv,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        prob_server_active=prob_server_active,
        prob_attack_round=prob_attack_round,
        **kwargs,
    )

    plot_perf(
        x_list=num_servers_list,
        disclosure_attack_result_given_x_func=disclosure_attack_result_given_x_func,
        x_label=r"$N_{\mathrm{server}}$",
        title=title,
        plot_name=f"plot_perf_vs_nservers_{plot_name_tail}",
    )
    log(INFO, "Done")


def plot_perf_vs_detection_gap_exp_factor(
    detection_gap_exp_factor_list: list[float],
    num_servers: int,
    num_target_servers: int,
    num_samples: int,
    w_model: bool,
    network_delay_rv: random_variable.RandomVariable = None,
    client_idle_time_rv: random_variable.RandomVariable = None,
    target_client_idle_time_rv: random_variable.RandomVariable = None,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable = None,
    prob_server_active: float = None,
    prob_attack_round: float = None,
    **kwargs,
):
    def disclosure_attack_result_given_x_func(
        detection_gap_exp_factor: float,
    ) -> disclosure_attack.DisclosureAttackResult:
        return sim_module.sim_w_disclosure_attack_w_joblib(
            num_clients=num_servers,
            num_servers=num_servers,
            num_target_servers=num_target_servers,
            num_samples=num_samples,
            w_model=w_model,
            network_delay_rv=network_delay_rv,
            client_idle_time_rv=client_idle_time_rv,
            target_client_idle_time_rv=target_client_idle_time_rv,
            num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            prob_server_active=prob_server_active,
            prob_attack_round=prob_attack_round,
            detection_gap_exp_factor=detection_gap_exp_factor,
            **kwargs,
        )

    title, plot_name_tail = get_title_and_plot_name_tail(
        w_model=w_model,
        num_target_servers=num_target_servers,
        num_samples=num_samples,
        num_servers=num_servers,
        network_delay_rv=network_delay_rv,
        client_idle_time_rv=client_idle_time_rv,
        target_client_idle_time_rv=target_client_idle_time_rv,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        prob_server_active=prob_server_active,
        prob_attack_round=prob_attack_round,
        **kwargs,
    )

    plot_perf(
        x_list=detection_gap_exp_factor_list,
        disclosure_attack_result_given_x_func=disclosure_attack_result_given_x_func,
        x_label=r"$\gamma$",
        title=title,
        plot_name=f"plot_perf_vs_detection_gap_exp_factor_{plot_name_tail}",
    )

    log(INFO, "Done")


def plot_perf_vs_num_servers_excluded_from_threshold(
    num_servers_excluded_from_threshold_list: list[float],
    num_servers: int,
    num_target_servers: int,
    num_samples: int,
    w_model: bool,
    network_delay_rv: random_variable.RandomVariable = None,
    client_idle_time_rv: random_variable.RandomVariable = None,
    target_client_idle_time_rv: random_variable.RandomVariable = None,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable = None,
    prob_server_active: float = None,
    prob_attack_round: float = None,
    **kwargs,
):
    def disclosure_attack_result_given_x_func(
        num_servers_excluded_from_threshold: int,
    ) -> disclosure_attack.DisclosureAttackResult:
        return sim_module.sim_w_disclosure_attack_w_joblib(
            num_clients=num_servers,
            num_servers=num_servers,
            num_target_servers=num_target_servers,
            num_samples=num_samples,
            w_model=w_model,
            network_delay_rv=network_delay_rv,
            client_idle_time_rv=client_idle_time_rv,
            target_client_idle_time_rv=target_client_idle_time_rv,
            num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            prob_server_active=prob_server_active,
            prob_attack_round=prob_attack_round,
            num_servers_excluded_from_threshold=num_servers_excluded_from_threshold,
            **kwargs,
        )

    title, plot_name_tail = get_title_and_plot_name_tail(
        w_model=w_model,
        num_target_servers=num_target_servers,
        num_samples=num_samples,
        num_servers=num_servers,
        network_delay_rv=network_delay_rv,
        client_idle_time_rv=client_idle_time_rv,
        target_client_idle_time_rv=target_client_idle_time_rv,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        prob_server_active=prob_server_active,
        prob_attack_round=prob_attack_round,
        **kwargs,
    )

    plot_perf(
        x_list=num_servers_excluded_from_threshold_list,
        disclosure_attack_result_given_x_func=disclosure_attack_result_given_x_func,
        x_label=r"$N_{\mathrm{server-excluded}}$",
        title=title,
        plot_name=f"plot_perf_vs_num_servers_excluded_from_threshold_{plot_name_tail}",
    )

    log(INFO, "Done")


def plot_perf_vs_prob_server_active(
    prob_server_active_list: list[float],
    num_servers: int,
    num_target_servers: int,
    num_samples: int,
    w_model: bool,
    network_delay_rv: random_variable.RandomVariable = None,
    client_idle_time_rv: random_variable.RandomVariable = None,
    target_client_idle_time_rv: random_variable.RandomVariable = None,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable = None,
    prob_server_active: float = None,
    prob_attack_round: float = None,
    **kwargs,
):
    def disclosure_attack_result_given_x_func(
        prob_server_active: float,
    ) -> disclosure_attack.DisclosureAttackResult:
        return sim_module.sim_w_disclosure_attack_w_joblib(
            num_clients=num_servers,
            num_servers=num_servers,
            num_target_servers=num_target_servers,
            num_samples=num_samples,
            w_model=w_model,
            network_delay_rv=network_delay_rv,
            client_idle_time_rv=client_idle_time_rv,
            target_client_idle_time_rv=target_client_idle_time_rv,
            num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            prob_server_active=prob_server_active,
            prob_attack_round=prob_attack_round,
            **kwargs,
        )

    title, plot_name_tail = get_title_and_plot_name_tail(
        w_model=w_model,
        num_target_servers=num_target_servers,
        num_samples=num_samples,
        num_servers=num_servers,
        network_delay_rv=network_delay_rv,
        client_idle_time_rv=client_idle_time_rv,
        target_client_idle_time_rv=target_client_idle_time_rv,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        prob_attack_round=prob_attack_round,
        **kwargs,
    )

    plot_perf(
        x_list=prob_server_active_list,
        disclosure_attack_result_given_x_func=disclosure_attack_result_given_x_func,
        x_label=r"$p_{\mathrm{server}}$",
        title=title,
        plot_name=f"plot_perf_vs_prob_server_active_{plot_name_tail}",
    )

    log(INFO, "Done")


def plot_perf_vs_max_msg_delivery_time(
    max_msg_delivery_time_list: list[float],
    num_servers: int,
    num_target_servers: int,
    num_samples: int,
    w_model: bool,
    network_delay_rv: random_variable.RandomVariable = None,
    client_idle_time_rv: random_variable.RandomVariable = None,
    target_client_idle_time_rv: random_variable.RandomVariable = None,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable = None,
    prob_server_active: float = None,
    prob_attack_round: float = None,
    **kwargs,
):
    def disclosure_attack_result_given_x_func(
        max_msg_delivery_time: float,
    ) -> disclosure_attack.DisclosureAttackResult:
        return sim_module.sim_w_disclosure_attack_w_joblib(
            num_clients=num_servers,
            num_servers=num_servers,
            num_target_servers=num_target_servers,
            num_samples=num_samples,
            w_model=w_model,
            network_delay_rv=network_delay_rv,
            client_idle_time_rv=client_idle_time_rv,
            target_client_idle_time_rv=target_client_idle_time_rv,
            num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            prob_server_active=prob_server_active,
            prob_attack_round=prob_attack_round,
            max_msg_delivery_time=max_msg_delivery_time,
            **kwargs,
        )

    title, plot_name_tail = get_title_and_plot_name_tail(
        w_model=w_model,
        num_target_servers=num_target_servers,
        num_samples=num_samples,
        num_servers=num_servers,
        network_delay_rv=network_delay_rv,
        client_idle_time_rv=client_idle_time_rv,
        target_client_idle_time_rv=target_client_idle_time_rv,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        prob_server_active=prob_server_active,
        prob_attack_round=prob_attack_round,
        **kwargs,
    )

    plot_perf(
        x_list=max_msg_delivery_time_list,
        disclosure_attack_result_given_x_func=disclosure_attack_result_given_x_func,
        x_label=r"$\Delta$",
        title=title,
        plot_name=f"plot_perf_vs_max_msg_delivery_time_{plot_name_tail}",
    )

    log(INFO, "Done")
