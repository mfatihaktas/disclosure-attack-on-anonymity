import joblib
import simpy

from src import utils
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
        num_target_servers: int,
        network_delay_rv: random_variable.RandomVariable,
        idle_time_rv: random_variable.RandomVariable,
        idle_time_rv_for_target_client: random_variable.RandomVariable,
        num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
    ):
        check(num_target_servers <= num_servers, "")

        self.env = env
        self.num_clients = num_clients
        self.num_servers = num_servers
        self.num_target_servers = num_target_servers
        self.network_delay_rv = network_delay_rv
        self.idle_time_rv = idle_time_rv
        self.idle_time_rv_for_target_client = idle_time_rv_for_target_client
        self.num_msgs_to_recv_for_get_request_rv = num_msgs_to_recv_for_get_request_rv

        # Network
        self.network = network_module.Network_wDelayAssignedPerMessage(
            env=self.env,
            _id="n",
            delay_rv=network_delay_rv,
        )

        # Servers
        self.server_list = []
        for server_rank in range(num_servers):
            server = server_module.Server(
                env=self.env,
                _id=f"{utils.get_server_id(server_rank)}",
            )
            server.next_hop = self.network
            self.server_list.append(server)

            self.network.register_server(server)

        # Clients
        for i in range(-1, num_clients):
            if i == -1:  # Target client
                client = client_module.Client(
                    env=self.env,
                    _id="c-target",
                    server_id_list=[
                        self.server_list[j % num_servers]._id
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

    def register_adversary(self, adversary: adversary_module.Adversary):
        self.adversary = adversary

        client_list = self.network.get_client_list()
        log(WARNING, "", client_list=client_list)
        self.network.get_client_list()[0].adversary = self.adversary

        for server in self.network.get_server_list():
            server.adversary = self.adversary

        log(DEBUG, "Registered \n", adversary=adversary)

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


def sim_w_disclosure_attack_w_joblib(
    num_clients: int,
    num_servers: int,
    network_delay_rv: random_variable.RandomVariable,
    idle_time_rv: random_variable.RandomVariable,
    idle_time_rv_for_target_client: random_variable.RandomVariable,
    num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
    num_target_servers: int,
    stability_threshold: float,
    num_samples: int,
) -> disclosure_attack.DisclosureAttackResult:
    def sim():
        env = simpy.Environment()

        # adversary = disclosure_attack.DisclosureAttack(
        adversary = disclosure_attack.DisclosureAttack_wBaselineInspection_wStationaryRounds(
            env=env,
            max_msg_delivery_time=network_delay_rv.max_value,
            stability_threshold=stability_threshold,
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
        f"{utils.get_server_id(server_rank)}" for server_rank in range(num_target_servers)
    )

    sim_result_list = joblib.Parallel(n_jobs=-1, prefer="threads")(
        [
            joblib.delayed(sim)()
            for _ in range(num_samples)
        ]
    )

    time_to_deanonymize_list = []
    num_rounds_list = []
    num_correct_target_server_sets = 0
    classification_result_list = []
    for sim_result in sim_result_list:
        target_server_id_set = sim_result[0]
        time_to_deanonymize = sim_result[1]
        num_rounds = sim_result[2]
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

        classification_result = disclosure_attack.ClassificationResult(
            num_targets_identified_as_target=num_targets_identified_as_target,
            num_targets_identified_as_non_target=num_target_servers - num_targets_identified_as_target,
            num_non_targets_identified_as_target=num_non_targets_identified_as_target,
            num_non_targets_identified_as_non_target=num_servers - num_target_servers - num_non_targets_identified_as_target,
        )
        classification_result_list.append(classification_result)

    return disclosure_attack.DisclosureAttackResult(
        time_to_deanonymize_list=time_to_deanonymize_list,
        num_rounds_list=num_rounds_list,
        target_server_set_accuracy=num_correct_target_server_sets / num_samples,
        classification_result_list=classification_result_list,
    )
