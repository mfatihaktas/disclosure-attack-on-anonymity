from src.prob import random_variable


def prob_at_least_n_arrivals(
    attack_window_length: float,
    arrival_rate: float,
    n: int,
):
    num_arrivals_rv = random_variable.Poisson(
        mu=attack_window_length * arrival_rate
    )
    return num_arrivals_rv.tail_prob(n)


def prob_server_active(
    network_delay_rv: random_variable.RandomVariable,
    client_idle_time_rv: random_variable.Exponential,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
) -> float:
    return prob_at_least_n_arrivals(
        attack_window_length=network_delay_rv.max_value,
        arrival_rate=client_idle_time_rv.mu,
        # TODO: Attention!
        n=num_msgs_to_recv_for_get_request_rv.min_value - 1,
    )


def prob_attack_round(
    network_delay_rv: random_variable.RandomVariable,
    target_client_idle_time_rv: random_variable.Exponential,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
) -> float:
    return prob_at_least_n_arrivals(
        attack_window_length=network_delay_rv.max_value,
        arrival_rate=target_client_idle_time_rv.mu,
        # TODO: Attention!
        n=num_msgs_to_recv_for_get_request_rv.min_value - 1,
    )
