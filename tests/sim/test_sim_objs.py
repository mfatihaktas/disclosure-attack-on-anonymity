import pytest
import simpy

from src.attack import disclosure_attack
from src.prob import random_variable
from src.sim import (
    client as client_module,
    network as network_module,
    server as server_module,
    tor as tor_module,
)

from src.debug_utils import *


@pytest.fixture(scope="module")
def env() -> simpy.Environment:
    return simpy.Environment()


@pytest.fixture(scope="module", params=[1])
def num_clients(request) -> int:
    return request.param


@pytest.fixture(scope="module", params=[1])
def num_servers(request) -> int:
    return request.param


@pytest.fixture(
    scope="module",
    params=[
        random_variable.Exponential(mu=1),
    ],
)
def idle_time_rv(request) -> random_variable.RandomVariable:
    return request.param


@pytest.fixture(
    scope="module",
    params=[
        random_variable.DiscreteUniform(min_value=1, max_value=1),
    ],
)
def num_msgs_to_recv_for_get_request_rv(request) -> random_variable.RandomVariable:
    return request.param


# @pytest.fixture
# def client_list(
#     env: simpy.Environment,
#     idle_time_rv: random_variable.RandomVariable,
#     num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
#     num_clients: int,
# ) -> list[client_module.Client]:
#     return [
#         client_module.Client(
#             env=env,
#             _id=f"c{i}",
#             idle_time_rv=idle_time_rv,
#             num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
#         )
#         for i in range(num_clients)
#     ]


# @pytest.fixture
# def server_list(
#     env: simpy.Environment,
#     num_servers: int,
# ) -> list[server_module.Server]:
#     return [
#         server_module.Server(
#             env=env,
#             _id=f"s{i}",
#         )
#         for i in range(num_servers)
#     ]


@pytest.fixture
def network_delay_rv() -> random_variable.RandomVariable:
    return random_variable.DiscreteUniform(min_value=1, max_value=5)


@pytest.fixture
def tor_system(
    env: simpy.Environment,
    num_clients: int,
    num_servers: int,
    network_delay_rv: random_variable.RandomVariable,
    idle_time_rv: random_variable.RandomVariable,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
) -> tor_module.TorSystem:
    tor_system = tor_module.TorSystem(
        env=env,
        num_clients=num_clients,
        num_servers=num_servers,
        network_delay_rv=network_delay_rv,
        idle_time_rv=idle_time_rv,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        num_target_servers=1,
    )

    return network


# def test_network_w_one_client_server(
#     network: network_module.Network,
# ):
#     env = network.env

#     env.run(
#         until=env.all_of(
#             server.process_recv_messages for server in network.get_server_list()
#         )
#     )
#     # env.run(until=100)


def test_DisclosureAttack(
    tor_system: tor_module.TorSystem,
):
    env = tor_system.env

    adversary = disclosure_attack.DisclosureAttack(
        env=env,
        max_msg_delivery_time=tor_system.network_delay_rv.max_value,
        error_percent=0.1,
    )

    tor_system.register_adversary(adversary=adversary)

    env.run(until=adversary.attack_completed_event)
