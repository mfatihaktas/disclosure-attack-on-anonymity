import simpy

from src.attack import (
    adversary as adversary_module,
    disclosure_attack,
)
from src.prob import random_variable
from src.sim import client as client_module
from src.sim import network as network_module
from src.sim import server as server_module

from src.debug_utils import check, DEBUG, INFO, log


class TorSystem():
    def __init__(
        self,
        env: simpy.Environment,
        num_clients: int,
        num_servers: int,
        network_delay_rv: random_variable.RandomVariable,
        idle_time_rv: random_variable.RandomVariable,
        num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
        num_target_servers: int,
    ):
        check(num_target_servers <= num_servers, "")

        self.env = env
        self.num_clients = num_clients
        self.num_servers = num_servers
        self.network_delay_rv = network_delay_rv
        self.idle_time_rv = idle_time_rv
        self.num_msgs_to_recv_for_get_request_rv = num_msgs_to_recv_for_get_request_rv
        self.num_target_servers = num_target_servers

        # Network
        self.network = network_module.Network_wDelayAssignedPerMessage(
            env=self.env,
            _id="n",
            delay_rv=network_delay_rv,
        )

        # Servers
        self.server_list = []
        for i in range(num_servers):
            server = server_module.Server(
                env=self.env,
                _id=f"s{i}",
            )
            server.next_hop = self.network
            self.server_list.append(server)

            self.network.register_server(server)

        # Clients
        for i in range(num_clients):
            client = client_module.Client(
                env=self.env,
                _id=f"c{i}",
                server_id_list=[
                    self.server_list[(i + j) % num_servers]._id
                    for j in range(num_target_servers)
                ],
                idle_time_rv=idle_time_rv,
                num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            )
            client.next_hop = self.network

            self.network.register_client(client)

    def register_adversary(self, adversary: adversary_module.Adversary):
        self.adversary = adversary

        self.network.get_client_list()[0].adversary = self.adversary

        for server in self.network.get_server_list():
            server.adversary = self.adversary

        log(DEBUG, "Registered \n", adversary=adversary)

    def __repr__(self):
        return (
            "TorSystem( \n"
            f"\t num_clients= {self.num_clients} \n"
            f"\t num_servers= {self.num_servers} \n"
            f"\t network_delay_rv= {self.network_delay_rv} \n"
            f"\t idle_time_rv= {self.idle_time_rv} \n"
            f"\t num_msgs_to_recv_for_get_request_rv= {self.num_msgs_to_recv_for_get_request_rv} \n"
            f"\t network= {self.network} \n"
            ")"
        )

    def get_attack_completion_time(self) -> float:
        return self.adversary.attack_completion_time

    def run(self):
        log(DEBUG, "Started")
        self.env.run(until=self.adversary.attack_completed_event)
        log(DEBUG, "Done")


def sim_time_to_deanonymize_w_disclosure_attack(
    num_clients: int,
    num_servers: int,
    network_delay_rv: random_variable.RandomVariable,
    idle_time_rv: random_variable.RandomVariable,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
    num_target_servers: int,
    num_samples: int,
    error_percent: float,
) -> list[float]:
    def sim() -> float:
        env = simpy.Environment()

        adversary = disclosure_attack.DisclosureAttack(
            env=env,
            max_msg_delivery_time=network_delay_rv.max_value,
            error_percent=error_percent,
        )

        tor = TorSystem(
            env=env,
            num_clients=num_clients,
            num_servers=num_servers,
            network_delay_rv=network_delay_rv,
            idle_time_rv=idle_time_rv,
            num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            num_target_servers=num_target_servers,
        )

        tor.register_adversary(adversary=adversary)
        tor.run()

        return tor.get_attack_completion_time()

    time_to_deanonymize_list = []
    for _ in range(num_samples):
        time_to_deanonymize = sim()
        log(INFO, "", time_to_deanonymize=time_to_deanonymize)
        time_to_deanonymize_list.append(time_to_deanonymize)

    return time_to_deanonymize_list
