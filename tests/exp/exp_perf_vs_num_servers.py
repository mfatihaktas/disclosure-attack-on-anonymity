from src.exp import plot
from src.prob import random_variable


if __name__ == "__main__":
    # num_servers_list = [3, 5]
    num_servers_list = [10]
    # num_servers_list = [3, 20, 100]
    # # num_servers_list = list(range(3, 20))
    # num_servers_list = [3, 10, 20, 50, 100, 200, 300, 400, 500]
    # num_servers_list = [3, 20, 50, 100, 200, 500, 1000, 1500, 2000, 2500, 3000]
    num_target_servers = 2
    num_samples = 1  # 5
    w_model = False
    # w_model = True

    # network_delay_rv = random_variable.Uniform(min_value=1, max_value=5)
    network_delay_rv = random_variable.Uniform(min_value=1, max_value=1)
    # client_idle_time_rv = random_variable.Uniform(min_value=0, max_value=1)
    mu = 1  # 0.05
    client_idle_time_rv = random_variable.Exponential(mu=mu)
    # target_client_idle_time_rv = random_variable.Uniform(min_value=4, max_value=6)
    target_client_idle_time_rv = random_variable.Exponential(mu=mu/2)
    num_msgs_to_recv_for_get_request_rv = random_variable.DiscreteUniform(min_value=1, max_value=1)

    prob_server_active = 0.5
    # prob_server_active = 1
    prob_attack_round = 0.5  # 0.4

    # stability_threshold = 0.003
    # max_stdev = 0.03
    # detection_gap_exp_factor = 1.2
    detection_gap_exp_factor = 2

    plot.plot_perf_vs_num_servers(
        num_servers_list=num_servers_list,
        num_target_servers=num_target_servers,
        num_samples=num_samples,
        w_model=w_model,
        network_delay_rv=network_delay_rv,
        client_idle_time_rv=client_idle_time_rv,
        target_client_idle_time_rv=target_client_idle_time_rv,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        prob_server_active=prob_server_active,
        prob_attack_round=prob_attack_round,
        # max_stdev=max_stdev,
        detection_gap_exp_factor=detection_gap_exp_factor,
    )
