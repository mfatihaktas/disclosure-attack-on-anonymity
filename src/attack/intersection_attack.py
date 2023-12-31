import heapq

import simpy

from src.attack import adversary as adversary_module
from src.debug_utils import *
from src.sim import client as client_module
from src.sim import message
from src.sim import node as node_module
from src.sim import server as server_module


class IntersectionAttack:
    def __init__(self):
        self.candidate_set = None

    def __repr__(self):
        return "IntersectionAttack( \n" f"\t candidate_set= {self.candidate_set} \n" ")"

    def get_number_of_candidates(self):
        return len(self.candidate_set)

    def update(self, candidate_set: set[str]):
        if self.candidate_set is None:
            self.candidate_set = candidate_set
        else:
            self.candidate_set = self.candidate_set.intersection(candidate_set)


class AttackWindow:
    def __init__(
        self,
        start_time: float,
        end_time: float,
    ):
        self.start_time = start_time
        self.end_time = end_time

        self.candidate_set = set()

    def add_candidate(self, candidate: str):
        self.candidate_set.add(candidate)

    def __lt__(self, other_attack_window) -> bool:
        return self.end_time < other_attack_window.end_time or (
            self.end_time == other_attack_window.end_time
            and self.begin_time < other_attack_window.begin_time
        )


class Adversary_wIntersectionAttack(adversary_module.Adversary):
    def __init__(
        self,
        env: simpy.Environment,
        max_delivery_time_for_adversary: float,
        num_target_client: int,
    ):
        super().__init__(
            env=env,
            max_delivery_time_for_adversary=max_delivery_time_for_adversary,
            num_target_client=num_target_client,
        )

        self.active_attack_window_heapq: list[AttackWindow] = []
        self.completed_attack_window_list: list[AttackWindow] = []

        self.intersection_attack = IntersectionAttack()

        self.attack_window_store = simpy.Store(env)
        self.interrupt_attack = None
        self.attack_process = env.process(self.run_attack())
        self.time_to_complete_attack = None

    def __repr__(self):
        return f"Adversary_wIntersectionAttack(max_delivery_time_for_adversary= {self.max_delivery_time_for_adversary})"

    def client_sent_msg(self, client_id: str):
        slog(
            DEBUG,
            self.env,
            self,
            "recved; starting new attack window",
            client_id=client_id,
        )

        attack_window = AttackWindow(
            start_time=self.env.now, end_time=self.env.now + self.max_delivery_time_for_adversary
        )

        heapq.heappush(self.active_attack_window_heapq, attack_window)

        # Note: Attack windows are consumed in `attack()` through `active_attack_window_heapq`.
        # The only reason to put messages in `attack_window_store` is to use it as a trigger to wake up
        # the attack loop when there is an attack window to process.
        self.attack_window_store.put(attack_window)

        if self.interrupt_attack:
            self.interrupt_attack.succeed()

    def server_recved_msg(self, server_id: str):
        slog(DEBUG, self.env, self, "recved", server_id=server_id)

        for attack_window in self.active_attack_window_heapq:
            attack_window.add_candidate(candidate=server_id)

    def run_attack(self):
        slog(DEBUG, self.env, self, "Started")

        attack_start_time = self.env.now
        while True:
            yield self.attack_window_store.get()

            attack_window = self.active_attack_window_heapq[0]
            wait_time = attack_window.end_time - self.env.now

            slog(DEBUG, self.env, self, "Waiting for trigger", wait_time=wait_time)
            self.interrupt_attack = self.env.event()
            yield self.env.timeout(wait_time) | self.interrupt_attack
            self.interrupt_attack = None

            if self.env.now - attack_window.end_time >= 0:
                attack_window = heapq.heappop(self.active_attack_window_heapq)

                slog(
                    DEBUG,
                    self.env,
                    self,
                    "Updating intersection attack",
                    candidate_set=attack_window.candidate_set,
                )
                self.intersection_attack.update(
                    candidate_set=attack_window.candidate_set
                )

                if (
                    self.intersection_attack.get_number_of_candidates()
                    == self.num_target_client
                ):
                    slog(
                        DEBUG,
                        self.env,
                        self,
                        "Found the target(s)!",
                        num_target_client=self.num_target_client,
                        target=self.intersection_attack.candidate_set,
                    )
                    break

            else:
                slog(DEBUG, self.env, self, "Wait interrupted by new attack window")
                self.attack_window_store.put(attack_window)

        self.time_to_complete_attack = self.env.now - attack_start_time
        slog(DEBUG, self.env, self, "Done", attack_completion_time=self.time_to_complete_attack)
