from src.exp import plot
from src.prob import random_variable


if __name__ == "__main__":
    max_delivery_time = 1  # 4
    max_msg_delivery_time_list = list(range(1, max_delivery_time + 1))
    # detection_gap_exp_factor = 0.5
    # detection_gap_exp_factor = 0.8
    detection_gap_exp_factor = 1
    # detection_gap_exp_factor = 1.5
    # detection_gap_exp_factor = 2.1

    num_servers = 50
    num_target_servers = 2
    num_samples = 1  # 3  # 5
    w_model = False
    # w_model = True

    network_delay_rv = random_variable.Uniform(min_value=1, max_value=max_delivery_time)
    mu = 1 / max_delivery_time  # 0.05
    client_idle_time_rv = random_variable.Exponential(mu=mu)
    target_client_idle_time_rv = random_variable.Exponential(mu=mu/2)
    num_msgs_to_recv_for_get_request_rv = random_variable.DiscreteUniform(min_value=1, max_value=1)

    prob_server_active = 0.5
    prob_attack_round = 0.5

    plot.plot_perf_vs_max_msg_delivery_time(
        max_msg_delivery_time_list=max_msg_delivery_time_list,
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
