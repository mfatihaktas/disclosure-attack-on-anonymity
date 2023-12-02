import pytest
import simpy

from src.attack import disclosure_attack
from src.prob import random_variable
from src.sim import tor as tor_module


@pytest.fixture(scope="module")
def env() -> simpy.Environment:
    return simpy.Environment()


@pytest.fixture(scope="module", params=[2])
def num_clients(request) -> int:
    return request.param


@pytest.fixture(scope="module", params=[2])
def num_servers(request) -> int:
    return request.param


@pytest.fixture(scope="module", params=[1])
def num_target_servers(request) -> int:
    return request.param


@pytest.fixture(
    scope="module",
    params=[
        random_variable.Exponential(mu=1),
    ],
)
def client_idle_time_rv(request) -> random_variable.RandomVariable:
    return request.param


@pytest.fixture(
    scope="module",
    params=[
        random_variable.DiscreteUniform(min_value=1, max_value=1),
    ],
)
def num_msgs_to_recv_for_get_request_rv(request) -> random_variable.RandomVariable:
    return request.param


@pytest.fixture
def network_delay_rv() -> random_variable.RandomVariable:
    return random_variable.DiscreteUniform(min_value=1, max_value=5)


@pytest.fixture
def tor_system(
    env: simpy.Environment,
    num_clients: int,
    num_servers: int,
    num_target_servers: int,
    network_delay_rv: random_variable.RandomVariable,
    client_idle_time_rv: random_variable.RandomVariable,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
) -> tor_module.TorSystem:
    return tor_module.TorSystem(
        env=env,
        num_clients=num_clients,
        num_servers=num_servers,
        network_delay_rv=network_delay_rv,
        client_idle_time_rv=client_idle_time_rv,
        num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
        num_target_servers=num_target_servers,
    )


def test_DisclosureAttack(
    tor_system: tor_module.TorSystem,
):
    env = tor_system.env
    adversary = disclosure_attack.DisclosureAttack(
        env=env,
        max_delivery_time_for_adversary=tor_system.network_delay_rv.max_value,
        error_percent=0.1,
    )

    tor_system.register_adversary(adversary=adversary)

    env.run(until=adversary.attack_completed_event)


def test_DisclosureAttack_wBaselineInspection_wStationaryRounds(
    tor_system: tor_module.TorSystem,
):
    env = tor_system.env
    adversary = disclosure_attack.DisclosureAttack_wBaselineInspection_wStationaryRounds(
        env=env,
        max_delivery_time_for_adversary=tor_system.network_delay_rv.max_value,
        stability_threshold=0.003,
    )

    tor_system.register_adversary(adversary=adversary)

    env.run(until=adversary.attack_completed_event)
