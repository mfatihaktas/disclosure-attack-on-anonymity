from src.model_for_paper import plot


if __name__ == "__main__":
    # non_target_arrival_rate = 1
    # attack_window_length = 2
    # num_target_packets = 1
    # num_target_servers = 1
    # alpha = 0.5

    # plot.plot_prob_error_vs_num_attack_rounds(
    #     non_target_arrival_rate=non_target_arrival_rate,
    #     attack_window_length=attack_window_length,
    #     num_target_packets=num_target_packets,
    #     num_target_servers=num_target_servers,
    #     alpha=0.5,
    # )

    max_prob_error = 0.1
    attack_window_length = 1
    num_target_packets = 1
    # num_target_packets = 5
    num_target_servers = 2
    alpha = 0.5

    plot.plot_attack_perf_vs_non_target_arrival_rate(
        max_prob_error=max_prob_error,
        attack_window_length=attack_window_length,
        num_target_packets=num_target_packets,
        num_target_servers=num_target_servers,
        alpha=alpha,
    )
