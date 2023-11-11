from src.exp import plot
from src.prob import random_variable


if __name__ == "__main__":
    # num_servers_excluded_from_threshold_list = [1]
    num_servers_excluded_from_threshold_list = [0, 1, 2]
    # num_servers_excluded_from_threshold_list = list(numpy.linspace(0.5, 2, num=6, endpoint=True))
    detection_gap_exp_factor = 0.5  # 1.2

    num_servers = 100
    num_target_servers = 2
    num_samples = 3  # 5
    # w_model = False
    w_model = True

    network_delay_rv = random_variable.Uniform(min_value=1, max_value=5)
    # idle_time_rv = random_variable.Exponential(mu=1)
    idle_time_rv = random_variable.Uniform(min_value=0, max_value=1)
    idle_time_rv_for_target_client = random_variable.Uniform(min_value=4, max_value=6)
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
        idle_time_rv=idle_time_rv,
        idle_time_rv_for_target_client=idle_time_rv_for_target_client,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        prob_server_active=prob_server_active,
        prob_attack_round=prob_attack_round,
        detection_gap_exp_factor=detection_gap_exp_factor,
    )
