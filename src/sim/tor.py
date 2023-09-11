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
        idle_time_rv_for_target_client: random_variable.RandomVariable,
        num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
        num_target_servers: int,
    ):
        check(num_target_servers <= num_servers, "")

        self.env = env
        self.num_clients = num_clients
        self.num_servers = num_servers
        self.network_delay_rv = network_delay_rv
        self.idle_time_rv = idle_time_rv
        self.idle_time_rv_for_target_client = idle_time_rv_for_target_client
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
                client = client_module.Client(
                    env=self.env,
                    _id=f"c-target",
                    server_id_list=[
                        self.server_list[(i + 1 + j) % num_servers]._id
                        for j in range(num_target_servers)
                    ],
                    idle_time_rv=idle_time_rv_for_target_client,
                    num_msgs_to_recv_for_get_request_rv=num_msgs_to_recv_for_get_request_rv,
                )

            else:
                client = client_module.Client(
                    env=self.env,
                    _id=f"c{i}",
                    server_id_list=[self.server_list[i % num_servers]._id],
                    idle_time_rv=idle_time_rv_for_target_client,
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
        return self.adversary.target_server_id_set

    def run(self):
        log(DEBUG, "Started")
        self.env.run(until=self.adversary.attack_completed_event)
        log(DEBUG, "Done")


@dataclasses.dataclass
class ClassificationResult:
    num_targets_identified_as_target: int
    num_targets_identified_as_non_target: int
    num_non_targets_identified_as_target: int
    num_non_targets_identified_as_non_target: int

    prob_target_identified_as_non_target: float = dataclasses.field(init=False)
    prob_non_target_identified_as_target: float = dataclasses.field(init=False)

    def __post_init__(self):
        self.prob_target_identified_as_non_target = (
            self.num_targets_identified_as_non_target
            / (self.num_targets_identified_as_target + self.num_targets_identified_as_non_target)
        )

        self.prob_non_target_identified_as_target = (
            self.num_non_targets_identified_as_target
            / (self.num_non_targets_identified_as_target + self.num_non_targets_identified_as_non_target)
        )


@dataclasses.dataclass
class DisclosureAttackResult:
    time_to_deanonymize_list: list[float]
    num_rounds_list: list[int]
    target_server_set_accuracy: float
    classification_result_list: list[ClassificationResult]


def sim_w_disclosure_attack(
    num_clients: int,
    num_servers: int,
    network_delay_rv: random_variable.RandomVariable,
    idle_time_rv: random_variable.RandomVariable,
    idle_time_rv_for_target_client: random_variable.RandomVariable,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
    num_target_servers: int,
    num_samples: int,
    diff_threshold: float,
) -> DisclosureAttackResult:
    def sim():
        env = simpy.Environment()

        # adversary = disclosure_attack.DisclosureAttack(
        adversary = disclosure_attack.DisclosureAttack_wBaselineInspection(
            env=env,
            max_msg_delivery_time=network_delay_rv.max_value,
            diff_threshold=diff_threshold,
        )

        tor = TorSystem(
            env=env,
            num_clients=num_clients,
            num_servers=num_servers,
            network_delay_rv=network_delay_rv,
            idle_time_rv=idle_time_rv,
            idle_time_rv_for_target_client=idle_time_rv_for_target_client,
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

    true_target_server_id_set = set(
        f"s{server_id}" for server_id in range(num_target_servers)
    )
    # log(WARNING, "", true_target_server_id_set=true_target_server_id_set)

    time_to_deanonymize_list = []
    num_rounds_list = []
    num_correct_target_server_sets = 0
    classification_result_list = []
    for _ in range(num_samples):
        target_server_id_set, time_to_deanonymize, num_rounds = sim()
        log(
            INFO, "",
            target_server_id_set=target_server_id_set,
            time_to_deanonymize=time_to_deanonymize,
            num_rounds=num_rounds,
        )

        time_to_deanonymize_list.append(time_to_deanonymize)
        num_rounds_list.append(num_rounds)

        num_correct_target_server_sets += int(true_target_server_id_set == target_server_id_set)

        # Append `classification_result`
        num_targets_identified_as_target = 0
        num_non_targets_identified_as_target = 0
        for target_server_id in target_server_id_set:
            if target_server_id in true_target_server_id_set:
                num_targets_identified_as_target += 1
            else:
                num_non_targets_identified_as_target += 1

        classification_result = ClassificationResult(
            num_targets_identified_as_target=num_targets_identified_as_target,
            num_targets_identified_as_non_target=num_target_servers - num_targets_identified_as_target,
            num_non_targets_identified_as_target=num_non_targets_identified_as_target,
            num_non_targets_identified_as_non_target=num_servers - num_target_servers - num_non_targets_identified_as_target,
        )
        classification_result_list.append(classification_result)

    return DisclosureAttackResult(
        time_to_deanonymize_list=time_to_deanonymize_list,
        num_rounds_list=num_rounds_list,
        target_server_set_accuracy=num_correct_target_server_sets / num_samples,
        classification_result_list=classification_result_list,
    )
