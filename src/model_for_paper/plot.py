from src.debug_utils import log, DEBUG, INFO
from src.model_for_paper import model
from src.plot_utils import NICE_BLUE, NICE_ORANGE, NICE_RED, plot


def plot_prob_error_vs_num_attack_rounds(
    non_target_arrival_rate: float,
    attack_window_length: float,
    num_target_packets: int,
    num_target_servers: int,
    alpha: float = 0.5,
):
    # Compute
    target_server = model.TargetServer(
        non_target_arrival_rate=non_target_arrival_rate,
        attack_window_length=attack_window_length,
        num_target_packets=num_target_packets,
        num_target_servers=num_target_servers,
    )
    non_target_server = model.NonTargetServer(
        non_target_arrival_rate=non_target_arrival_rate,
        attack_window_length=attack_window_length,
        num_target_packets=num_target_packets,
    )

    target_detection_threshold = model.get_detection_threshold(
        non_target_arrival_rate=non_target_arrival_rate,
        attack_window_length=attack_window_length,
        num_target_packets=num_target_packets,
        num_target_servers=num_target_servers,
        alpha=alpha,
    )
    log(
        INFO, "",
        target_detection_threshold=target_detection_threshold,
    )

    num_attack_rounds_list = []
    prob_identifying_target_as_non_target_list = []
    prob_identifying_non_target_as_target_list = []
    for num_attack_rounds in range(1, 100):
        print(f"> num_attack_rounds= {num_attack_rounds}")
        num_attack_rounds_list.append(num_attack_rounds)

        prob_identifying_target_as_non_target = target_server.prob_error(
            num_attack_rounds=num_attack_rounds,
            threshold_to_identify_as_target=target_detection_threshold,
        )
        prob_identifying_target_as_non_target_list.append(prob_identifying_target_as_non_target)

        prob_identifying_non_target_as_target = non_target_server.prob_error(
            num_attack_rounds=num_attack_rounds,
            threshold_to_identify_as_target=target_detection_threshold,
        )
        prob_identifying_non_target_as_target_list.append(prob_identifying_non_target_as_target)

    log(
        DEBUG, "",
        num_attack_rounds_list=num_attack_rounds_list,
        prob_identifying_target_as_non_target_list=prob_identifying_target_as_non_target_list,
        prob_identifying_non_target_as_target_list=prob_identifying_non_target_as_target_list,
    )

    # Plot
    fontsize = 14
    num_columns = 2
    fig, axs = plot.subplots(1, num_columns)

    ax = axs[0]
    plot.sca(ax)
    plot.errorbar(num_attack_rounds_list, prob_identifying_target_as_non_target_list, color=NICE_BLUE, marker="o")
    plot.xlabel(r"$N_{\mathrm{attack-round}}$", fontsize=fontsize)
    # plot.ylabel(r"$\mathrm{Pr}\{\mathtext{target as non-target}\}$", fontsize=fontsize)
    plot.ylabel("Pr(target as non-target)", fontsize=fontsize)

    ax = axs[1]
    plot.sca(ax)
    plot.errorbar(num_attack_rounds_list, prob_identifying_non_target_as_target_list, color=NICE_ORANGE, marker="o")
    plot.xlabel(r"$N_{\mathrm{attack-round}}$", fontsize=fontsize)
    # plot.ylabel(r"$\mathrm{Pr}\{\mathtext{non-target as target}\}$", fontsize=fontsize)
    plot.ylabel("Pr(non-target as target)", fontsize=fontsize)

    title = (
        r"$\mu_{\mathrm{non-target}} =$" + fr"${non_target_arrival_rate}$, "
        r"$T_{\mathrm{attack-win}} =$" + fr"${attack_window_length}$, "
        r"$N_{\mathrm{target-packets}} =$" + fr"${num_target_packets}$, "
        r"$N_{\mathrm{target-servers}} =$" + fr"${num_target_servers}$, "
        fr"$\alpha = {alpha}$"
    )
    st = plot.suptitle(title, fontsize=fontsize)  # , y=1.1

    fig.set_size_inches(num_columns * 6, 4)
    plot.subplots_adjust(hspace=0.25, wspace=0.25)

    plot_name = (
        "plot_prob_error_vs_num_attack_rounds"
        f"_ntarget_ar_rate_{non_target_arrival_rate}"
        f"_attack_win_{attack_window_length}"
        f"_ntarget_packets_{num_target_packets}"
        f"_ntarget_servers_{num_target_servers}"
        f"_alpha_{alpha}"
    )
    plot.savefig(f"plots/{plot_name}.pdf", bbox_extra_artists=[st], bbox_inches="tight")
    plot.gcf().clear()
