from src.exp import plot_w_model


if __name__ == "__main__":
    num_target_servers = 2
    num_servers_list = [3]
    # num_servers_list = [3, 20, 100]
    # # num_servers_list = list(range(3, 20))
    # num_servers_list = [3, 10, 20, 50, 100, 200, 300, 400]
    # num_servers_list = [3, 20, 50, 100, 200, 500, 1000, 1500, 2000, 2500, 3000]
    num_samples = 1  # 5

    prob_target_server_recv = 1  # 0.6
    prob_non_target_server_recv = 0.3

    # stability_threshold = 0.003
    # plot_w_model.plot_time_to_deanonymize_vs_num_servers(
    #     num_target_servers=num_target_servers,
    #     num_servers_list=num_servers_list,
    #     prob_target_server_recv=prob_target_server_recv,
    #     prob_non_target_server_recv=prob_non_target_server_recv,
    #     num_samples=num_samples,
    #     stability_threshold=stability_threshold,
    # )

    max_stdev = 0.01
    plot_w_model.plot_time_to_deanonymize_vs_num_servers(
        num_target_servers=num_target_servers,
        num_servers_list=num_servers_list,
        prob_target_server_recv=prob_target_server_recv,
        prob_non_target_server_recv=prob_non_target_server_recv,
        num_samples=num_samples,
        max_stdev=max_stdev,
    )
