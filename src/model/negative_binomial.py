import collections
import random


def sim_num_trials_until_k_successes(k: int, p: float) -> int:
    num_trials = 0
    num_successes = 0
    while num_successes < k:
        if random.random() <= p:
            num_successes += 1

        num_trials += 1

    return num_trials


def sim_sorted_num_trials_over_channels_until_m_channels_reach_k_successes(
    n: int,
    m: int,
    k: int,
    p: float,
) -> int:
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
