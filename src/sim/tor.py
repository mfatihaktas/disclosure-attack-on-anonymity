import dataclasses
import simpy

from src.attack import (
    adversary as adversary_module,
    disclosure_attack,
)
from src.prob import random_variable
from src.sim import client as client_module
from src.sim import network as network_module
from src.sim import server as server_module

from src.debug_utils import check, DEBUG, INFO, log, WARNING


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
        for i in range(-1, num_clients):
            if i == -1:  # Target client
                server_id_list = [
                    self.server_list[(i + 1 + j) % num_servers]._id
                    for j in range(num_target_servers)
                ]

            else:
                server_id_list = [self.server_list[i % num_servers]._id]

            client = client_module.Client(
                env=self.env,
                _id=f"c{i}",
                server_id_list=server_id_list,
                idle_time_rv=idle_time_rv,
                num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
            )
            client.next_hop = self.network

            self.network.register_client(client)

    def register_adversary(self, adversary: adversary_module.Adversary):
        self.adversary = adversary

        client_list = self.network.get_client_list()
        log(WARNING, "", client_list=client_list)
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
        return self.adversary.time_to_complete_attack

    def get_num_rounds(self) -> int:
        return self.adversary.num_sample_sets_collected

    def get_target_server_ids(self) -> set[str]:
        return self.adversary.target_server_ids

    def run(self):
        log(DEBUG, "Started")
        self.env.run(until=self.adversary.attack_completed_event)
        log(DEBUG, "Done")


@dataclasses.dataclass
class DisclosureAttackResult:
    time_to_deanonymize_list: list[float]
    num_rounds_list: list[int]
    target_server_accuracy: float


def sim_w_disclosure_attack(
    num_clients: int,
    num_servers: int,
    network_delay_rv: random_variable.RandomVariable,
    idle_time_rv: random_variable.RandomVariable,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
    num_target_servers: int,
    num_samples: int,
    error_percent: float,
) -> DisclosureAttackResult:
    def sim():
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

        return (
            tor.get_target_server_ids(),
            tor.get_attack_completion_time(),
            tor.get_num_rounds()
        )

    true_target_server_ids = set(
        f"s{server_id}" for server_id in range(num_target_servers)
    )
    # log(WARNING, "", true_target_server_ids=true_target_server_ids)

    time_to_deanonymize_list = []
    num_rounds_list = []
    num_correct_target_server_ids = 0
    for _ in range(num_samples):
        target_server_ids, time_to_deanonymize, num_rounds = sim()
        log(
            INFO, "",
            target_server_ids=target_server_ids,
            time_to_deanonymize=time_to_deanonymize,
            num_rounds=num_rounds,
        )

        time_to_deanonymize_list.append(time_to_deanonymize)
        num_rounds_list.append(num_rounds)

        num_correct_target_server_ids += int(true_target_server_ids == target_server_ids)

    return DisclosureAttackResult(
        time_to_deanonymize_list=time_to_deanonymize_list,
        num_rounds_list=num_rounds_list,
        target_server_accuracy=num_correct_target_server_ids / num_samples
    )
