import collections
import numpy
import random

from src.debug_utils import log, INFO
from src.plot_utils import NICE_BLUE, plot


def sample_num_trials_until_k_successes(k: int, p: float) -> int:
    num_trials = 0
    num_successes = 0
    while num_successes < k:
        if random.random() <= p:
            num_successes += 1

        num_trials += 1

    return num_trials


def sample_sorted_num_trials_over_channels_until_m_channels_reach_k_successes(
    n: int,
    m: int,
    k: int,
    p: float,
) -> list[int]:
    channel_id_to_num_successes_map = collections.defaultdict(int)

    num_trails = 0
    channels_with_k_successes = set()
    while len(channels_with_k_successes) < m:
        for channel_id in range(n):
            if random.random() <= p:
                channel_id_to_num_successes_map[channel_id] += 1

            if (
                channel_id not in channels_with_k_successes
                and channel_id_to_num_successes_map[channel_id] == k
            ):
                channels_with_k_successes.add(channel_id)

        num_trails += 1

    return sorted(channel_id_to_num_successes_map.values())


def sim_sorted_num_trials_over_channels_until_m_channels_reach_k_successes(
    n: int,
    m: int,
    k: int,
    p: float,
    num_samples: int,
) -> list[int]:
    sorted_num_trials_list = [[] for _ in range(n)]

    for s in range(num_samples):
        log(INFO, f">> s= {s}")

        sorted_num_trials = sample_sorted_num_trials_over_channels_until_m_channels_reach_k_successes(
            n=n, m=m, k=k, p=p,
        )

        for i in range(n):
            sorted_num_trials_list[i].append(sorted_num_trials[i])

    return sorted_num_trials_list


def plot_sorted_num_trials_over_channels(
    n: int,
    m: int,
    k: int,
    p: float,
    num_samples: int,
):
    log(INFO, "Started", n=n, m=m, k=k, p=p, num_samples=num_samples)

    sorted_num_trials_over_channels = sim_sorted_num_trials_over_channels_until_m_channels_reach_k_successes(
        n=n, m=m, k=k, p=p, num_samples=num_samples
    )
    E_num_trials_list = [
        numpy.mean(ls) for ls in sorted_num_trials_over_channels
    ]
    stdev_num_trials_list = [
        numpy.std(ls) for ls in sorted_num_trials_over_channels
    ]

    # Plot
    fontsize = 14

    x_list = list(range(1, n + 1))
    plot.errorbar(x_list, E_num_trials_list, yerr=stdev_num_trials_list, color=NICE_BLUE, marker="o")
    plot.xlabel("Order index", fontsize=fontsize)
    plot.ylabel("Number of successes", fontsize=fontsize)

    title = (
        fr"$n = {n}$, "
        fr"$m = {m}$, "
        fr"$k = {k}$, "
        fr"$p = {p}$, "
        r"$N_{\mathrm{samples}} =$" + fr"${num_samples}$"
    )
    plot.title(title, fontsize=fontsize)  # , y=1.1

    plot.gcf().set_size_inches(6, 4)
    plot_name = (
        "plot_sorted_num_trials_over_channels"
        f"_n_{n}"
        f"_m_{m}"
        f"_k_{k}"
        f"_p_{round(p, 2)}"
    )
    plot.savefig(f"plots/{plot_name}.pdf", bbox_inches="tight")
    plot.gcf().clear()

    log(INFO, "Done")
