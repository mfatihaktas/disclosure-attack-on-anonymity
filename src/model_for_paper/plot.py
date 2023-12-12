import dataclasses
import numpy

from typing import Callable

from src.debug_utils import log, DEBUG, ERROR, INFO
from src.model_for_paper import model
from src.plot_utils import NICE_BLUE, NICE_ORANGE, NICE_RED, plot


def plot_prob_error_vs_num_attack_rounds(
    non_target_arrival_rate: float,
    attack_window_length: float,
    num_target_packets: int,
    num_target_servers: int,
    alpha: float = 0.5,
):
    exp_setup = model.ExpSetup_wTargetVsNonTarget(
        non_target_arrival_rate=non_target_arrival_rate,
        attack_window_length=attack_window_length,
        num_target_packets=num_target_packets,
        num_target_servers=num_target_servers,
        alpha=alpha,
    )

    num_attack_rounds_list = []
    prob_identifying_target_as_non_target_list = []
    prob_identifying_non_target_as_target_list = []
    for num_attack_rounds in range(1, 100):
        print(f"> num_attack_rounds= {num_attack_rounds}")
        num_attack_rounds_list.append(num_attack_rounds)

        prob_identifying_target_as_non_target = exp_setup.prob_target_as_non_target(
            num_attack_rounds=num_attack_rounds,
        )
        prob_identifying_target_as_non_target_list.append(prob_identifying_target_as_non_target)

        prob_identifying_non_target_as_target = exp_setup.prob_non_target_as_target(
            num_attack_rounds=num_attack_rounds,
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


@dataclasses.dataclass
class AttackPerfPoint:
    x: float
    num_attack_rounds: int
    prob_target_as_non_target: float
    prob_non_target_as_target: float
    prob_target_active: float
    prob_non_target_active: float


@dataclasses.dataclass
class AttackPerf:
    perf_point_list: list[AttackPerfPoint] = dataclasses.field(default_factory=list)

    def add(self, perf_point: AttackPerfPoint):
        self.perf_point_list.append(perf_point)

    def x_list(self) -> list:
        return [p.x for p in self.perf_point_list]

    def num_attack_rounds_list(self) -> list:
        return [p.num_attack_rounds for p in self.perf_point_list]

    def prob_target_as_non_target_list(self) -> list:
        return [p.prob_target_as_non_target for p in self.perf_point_list]

    def prob_non_target_as_target_list(self) -> list:
        return [p.prob_non_target_as_target for p in self.perf_point_list]

    def prob_target_active_list(self) -> list:
        return [p.prob_target_active for p in self.perf_point_list]

    def prob_non_target_active_list(self) -> list:
        return [p.prob_non_target_active for p in self.perf_point_list]


def _plot_attack_perf(
    attack_perf: AttackPerf,
    x_label: str,
    title: str,
    plot_name: str,
):
    x_list = attack_perf.x_list()
    num_attack_rounds_list = attack_perf.num_attack_rounds_list()
    prob_target_as_non_target_list = attack_perf.prob_target_as_non_target_list()
    prob_non_target_as_target_list = attack_perf.prob_non_target_as_target_list()
    prob_target_active_list = attack_perf.prob_target_active_list()
    prob_non_target_active_list = attack_perf.prob_non_target_active_list()

    fontsize = 14
    num_columns = 4
    fig, axs = plot.subplots(1, num_columns)

    i = 0
    ax = axs[i]
    plot.sca(ax)
    plot.plot(x_list, prob_target_active_list, label="target", color="r", marker="x")
    plot.plot(x_list, prob_non_target_active_list, label="non-target", color="b", marker="x")
    plot.legend(loc="best", framealpha=0.5, fontsize=fontsize)
    plot.xlabel(x_label, fontsize=fontsize)
    plot.ylabel(r"$\mathrm{Pr}\{\mathrm{active}\}$", fontsize=fontsize)

    i += 1
    ax = axs[i]
    ax.set_yscale("log")
    plot.sca(ax)
    plot.errorbar(x_list, num_attack_rounds_list, color=NICE_BLUE, marker="o")
    plot.xlabel(x_label, fontsize=fontsize)
    plot.ylabel(r"$N_{\mathrm{attack-round}}$", fontsize=fontsize)

    i += 1
    ax = axs[i]
    plot.sca(ax)
    plot.errorbar(x_list, prob_target_as_non_target_list, color=NICE_RED, marker="o")
    plot.xlabel(x_label, fontsize=fontsize)
    plot.ylabel(r"$\mathrm{Pr}\{\mathrm{target-as-non-target}\}$", fontsize=fontsize)

    i += 1
    ax = axs[i]
    plot.sca(ax)
    plot.errorbar(x_list, prob_non_target_as_target_list, color=NICE_ORANGE, marker="o")
    plot.xlabel(x_label, fontsize=fontsize)
    plot.ylabel(r"$\mathrm{Pr}\{\mathrm{non-target-as-target}\}$", fontsize=fontsize)

    st = plot.suptitle(title, fontsize=fontsize)  # , y=1.1

    fig.set_size_inches(num_columns * 6, 4)
    plot.subplots_adjust(hspace=0.25, wspace=0.25)

    plot.savefig(f"plots/{plot_name}.pdf", bbox_extra_artists=[st], bbox_inches="tight")
    plot.gcf().clear()


def _get_attack_perf_to_plot(
    x_list: list,
    attack_perf_point_for_given_x: Callable,
) -> AttackPerf:
    attack_perf = AttackPerf()

    for x in x_list:
        attack_perf_point = attack_perf_point_for_given_x(x)
        if attack_perf_point:
            attack_perf.add(attack_perf_point)

    return attack_perf


def plot_attack_perf_vs_non_target_arrival_rate(
    max_prob_error: float,
    attack_window_length: float,
    num_target_packets: int,
    num_target_servers: int,
    alpha: float = 0.5,
):
    log(
        INFO, "",
        max_prob_error=max_prob_error,
        attack_window_length=attack_window_length,
        num_target_packets=num_target_packets,
        num_target_servers=num_target_servers,
        alpha=alpha,
    )

    def attack_perf_point_for_given_x(
        non_target_arrival_rate: float,
    ) -> AttackPerfPoint:
        exp_setup = model.ExpSetup_wTargetVsNonTarget(
            non_target_arrival_rate=non_target_arrival_rate,
            attack_window_length=attack_window_length,
            num_target_packets=num_target_packets,
            num_target_servers=num_target_servers,
            alpha=alpha,
        )
        try:
            num_attack_rounds = exp_setup.get_min_num_attack_rounds(max_prob_error=max_prob_error)
            log(
                INFO, "",
                num_attack_rounds=num_attack_rounds,
                non_target_arrival_rate=non_target_arrival_rate,
            )
        except OverflowError:
            log(
                ERROR, "OverflowError",
                non_target_arrival_rate=non_target_arrival_rate,
            )
            return None

        perf_point = AttackPerfPoint(
            x=non_target_arrival_rate,
            num_attack_rounds=num_attack_rounds,
            prob_target_as_non_target=exp_setup.prob_target_as_non_target(
                num_attack_rounds=num_attack_rounds
            ),
            prob_non_target_as_target=exp_setup.prob_non_target_as_target(
                num_attack_rounds=num_attack_rounds
            ),
            prob_target_active=exp_setup.prob_target_active,
            prob_non_target_active=exp_setup.prob_non_target_active,
        )
        log(
            INFO, "",
            non_target_arrival_rate=non_target_arrival_rate,
            perf_point=perf_point,
        )

        return perf_point

    attack_perf = _get_attack_perf_to_plot(
        x_list=numpy.linspace(
            # start=0.1 / attack_window_length,
            start=0,
            stop=10 / attack_window_length,
            num=50,
        ),
        attack_perf_point_for_given_x=attack_perf_point_for_given_x,
    )
    # log(
    #     INFO, "",
    #     attack_perf=attack_perf,
    # )

    title = (
        r"$\mathrm{max-}p_{\mathrm{error}} =$" + fr"${max_prob_error}$, "
        r"$T_{\mathrm{attack-win}} =$" + fr"${attack_window_length}$, "
        r"$N_{\mathrm{target-packets}} =$" + fr"${num_target_packets}$, "
        r"$N_{\mathrm{target-servers}} =$" + fr"${num_target_servers}$, "
        fr"$\alpha = {alpha}$"
    )
    plot_name = (
        "plot_attack_perf_vs_non_target_arrival_rate"
        f"_max_prob_error_{max_prob_error}"
        f"_attack_win_{attack_window_length}"
        f"_ntarget_packets_{num_target_packets}"
        f"_ntarget_servers_{num_target_servers}"
        f"_alpha_{alpha}"
    )

    _plot_attack_perf(
        attack_perf=attack_perf,
        x_label=r"$\mu_{\mathrm{non-target}}$",
        title=title,
        plot_name=plot_name,
    )
