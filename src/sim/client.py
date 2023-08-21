import random
import simpy

from src.attack import adversary as adversary_module
from src.prob import random_variable
from src.sim import message, node

from src.debug_utils import DEBUG, slog


class Client(node.Node):
    def __init__(
        self,
        env: simpy.Environment,
        _id: str,
        server_id_list: list[int],
        idle_time_rv: random_variable.RandomVariable,
        num_msgs_to_recv_for_get_request_rv: random_variable.RandomVariable,
    ):
        super().__init__(env=env, _id=_id)
        self.server_id_list = server_id_list
        self.idle_time_rv = idle_time_rv
        self.num_msgs_to_recv_for_get_request_rv = num_msgs_to_recv_for_get_request_rv

        # To be set while getting connected to the network
        self.next_hop = None

        self.adversary: adversary_module.Adversary = None

        self.token_store = simpy.Store(env)
        self.token_store.put(1)
        self.process_send_messages = env.process(self.send_messages())

        self.num_msgs_to_recv_for_get_request = None
        self.num_msgs_recved_for_get_request = 0

    def __repr__(self):
        return (
            "Client( \n"
            f"{super().__repr__()} \n"
            f"\t server_id_list= {self.server_id_list} \n"
            f"\t idle_time_rv= {self.idle_time_rv} \n"
            ")"
        )

        # return f"Client(id= {self._id})"

    def put(self, msg: message.Message):
        slog(DEBUG, self.env, self, "recved", msg=msg)

        self.num_msgs_recved_for_get_request += 1
        if self.num_msgs_recved_for_get_request == self.num_msgs_to_recv_for_get_request:
            slog(
                DEBUG, self.env, self,
                "received all msgs for GET request",
                num_msgs_recved_for_get_request=self.num_msgs_recved_for_get_request
            )

            if self.adversary:
                self.adversary.client_completed_get_request(
                    num_msgs_recved_for_get_request=self.num_msgs_recved_for_get_request
                )

            self.token_store.put(1)

    def send_messages(self):
        slog(DEBUG, self.env, self, "started")

        msg_id = 0
        while True:
            yield self.token_store.get()

            # Wait idle
            idle_time = self.idle_time_rv.sample()
            slog(
                DEBUG, self.env, self, "waiting idle", idle_time=idle_time
            )
            yield self.env.timeout(idle_time)

            # Send GET request
            server_id = random.choice(self.server_id_list)
            self.num_msgs_to_recv_for_get_request = self.num_msgs_to_recv_for_get_request_rv.sample()
            msg = message.GetRequest(
                _id=msg_id,
                src_id=self._id,
                dst_id=server_id,
                num_msgs_to_recv=self.num_msgs_to_recv_for_get_request,
            )
            slog(DEBUG, self.env, self, "sending", msg=msg)
            self.next_hop.put(msg)
            if self.adversary:
                self.adversary.client_sent_msg(msg=msg)

            # Prepare for response
            self.num_msgs_recved_for_get_request = 0

            msg_id += 1

        slog(DEBUG, self.env, self, "done")
