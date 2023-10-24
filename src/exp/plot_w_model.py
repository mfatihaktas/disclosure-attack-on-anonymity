from src.exp import utils

from src.debug_utils import log, DEBUG, INFO
from src.plot_utils import NICE_BLUE, NICE_ORANGE, NICE_RED, plot


def plot_time_to_deanonymize_vs_num_servers(
    num_target_servers: int,
    num_servers_list: list[int],
    prob_server_active: float,
    prob_attack_round: float,
    num_samples: int,
    **kwargs,
):
    results_dict = utils.get_results_to_plot_w_model(
        num_target_servers=num_target_servers,
        num_servers_list=num_servers_list,
        prob_server_active=prob_server_active,
        prob_attack_round=prob_attack_round,
        num_samples=num_samples,
        **kwargs,
    )

    # Plot
    fontsize = 14
    num_columns = 3
    fig, axs = plot.subplots(1, num_columns)

    ax = axs[0]
    plot.sca(ax)
    plot.xlabel("Number of candidate servers", fontsize=fontsize)
    # plot.errorbar(num_servers_list, E_num_rounds_list, yerr=std_num_rounds_list, color=NICE_BLUE, marker="o")
    # plot.ylabel("Number of rounds", fontsize=fontsize)
    plot.errorbar(num_servers_list, results_dict["E_time_to_deanonymize_list"], yerr=results_dict["std_time_to_deanonymize_list"], color=NICE_BLUE, marker="o")
    plot.ylabel("Time-to-deanonymize", fontsize=fontsize)

    ax = axs[1]
    plot.sca(ax)
    plot.errorbar(num_servers_list, results_dict["E_prob_target_identified_as_non_target_list"], yerr=results_dict["std_prob_target_identified_as_non_target_list"], color=NICE_ORANGE, marker="o")
    plot.xlabel("Number of candidate servers", fontsize=fontsize)
    plot.ylabel(r"$\mathrm{Pr}\{$target identified as non-target$\}$", fontsize=fontsize)

    ax = axs[2]
    plot.sca(ax)
    plot.errorbar(num_servers_list, results_dict["E_prob_non_target_identified_as_target_list"], yerr=results_dict["std_prob_non_target_identified_as_target_list"], color=NICE_RED, marker="o")
    plot.xlabel("Number of candidate servers", fontsize=fontsize)
    plot.ylabel(r"$\mathrm{Pr}\{$non-target identified as target$\}$", fontsize=fontsize)

    title = (
        r"$N_{\mathrm{target}} =$" + fr"${num_target_servers}$, "
        r"$p_{\mathrm{server}} =$" + fr"${prob_server_active}$, "
        r"$p_{\mathrm{client}} =$" + fr"${prob_attack_round}$, "
        r"$N_{\mathrm{samples}} =$" + fr"${num_samples}$"
    )
    if "max_stdev" in kwargs:
        title += ", " + r"$\sigma_{\mathrm{max}} =$" + fr"${kwargs['max_stdev']}$"
    plot.suptitle(title, fontsize=fontsize)

    fig.set_size_inches(num_columns * 6, 4)
    plot.subplots_adjust(hspace=0.25, wspace=0.25)

    plot_name = (
        "plot_time_to_deanon_vs_num_servers"
        f"_ntarget_{num_target_servers}"
        f"_pserver_{prob_server_active}"
        f"_pclient_{prob_attack_round}"
        f"_num_samples_{num_samples}"
    )
    plot.savefig(f"plots/{plot_name}.pdf", bbox_inches="tight")

    plot.gcf().clear()
    log(INFO, "Done")
