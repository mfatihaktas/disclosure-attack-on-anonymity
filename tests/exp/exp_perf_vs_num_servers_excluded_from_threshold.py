from src.exp import plot
from src.prob import random_variable


if __name__ == "__main__":
    # num_servers_excluded_from_threshold_list = [1]
    # num_servers_excluded_from_threshold_list = [0, 1, 2]
    # num_servers_excluded_from_threshold_list = list(range(10))
    num_servers_excluded_from_threshold_list = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 49]
    # detection_gap_exp_factor = 0.5
    # detection_gap_exp_factor = 0.8
    # detection_gap_exp_factor = 1
    # detection_gap_exp_factor = 1.5
    # detection_gap_exp_factor = 2.1
    detection_gap_exp_factor = 3

    num_servers = 50
    num_target_servers = 2
    num_samples = 3  # 5
    # w_model = False
    w_model = True

    # network_delay_rv = random_variable.Uniform(min_value=1, max_value=5)
    network_delay_rv = random_variable.Uniform(min_value=1, max_value=1)
    # client_idle_time_rv = random_variable.Uniform(min_value=0, max_value=1)
    mu = 1  # 0.05
    client_idle_time_rv = random_variable.Exponential(mu=mu)
    # target_client_idle_time_rv = random_variable.Uniform(min_value=4, max_value=6)
    target_client_idle_time_rv = random_variable.Exponential(mu=mu/2)
    num_msgs_to_recv_for_get_request_rv = random_variable.DiscreteUniform(min_value=1, max_value=1)

    prob_server_active = 0.5
    prob_attack_round = 0.5

    plot.plot_perf_vs_num_servers_excluded_from_threshold(
        num_servers_excluded_from_threshold_list=num_servers_excluded_from_threshold_list,
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
    )
