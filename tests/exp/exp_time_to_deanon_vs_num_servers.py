from src.exp import plot
from src.prob import random_variable


if __name__ == "__main__":
    network_delay_rv = random_variable.Uniform(min_value=1, max_value=5)
    # idle_time_rv = random_variable.Exponential(mu=1)
    idle_time_rv = random_variable.Uniform(min_value=0, max_value=1)
    idle_time_rv_for_target_client = random_variable.Uniform(min_value=4, max_value=6)
    num_msgs_to_recv_for_get_request_rv = random_variable.DiscreteUniform(min_value=1, max_value=1)
    num_target_servers = 2
    num_servers_list = [3, 4]
    # num_servers_list = list(range(3, 20))
    # num_servers_list = [3, 10, 20, 50, 100, 200, 300, 400]
    # num_servers_list = [3, 20, 50, 100, 200, 500, 1000, 1500, 2000, 2500, 3000]
    stability_threshold = 0.003
    num_samples = 1  # 5

    plot.plot_time_to_deanonymize_vs_num_servers(
        network_delay_rv=network_delay_rv,
        idle_time_rv=idle_time_rv,
        idle_time_rv_for_target_client=idle_time_rv_for_target_client,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        num_target_servers=num_target_servers,
        num_servers_list=num_servers_list,
        stability_threshold=stability_threshold,
        num_samples=num_samples,
    )
