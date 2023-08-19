import simpy

from src.attack import adversary as adversary_module
from src.sim import message, node

from src.debug_utils import DEBUG, slog


class Server(node.Node):
    def __init__(
        self,
        env: simpy.Environment,
        _id: str,
    ):
        super().__init__(env=env, _id=_id)

        self.next_hop = None

        self.num_msgs_sent = 0
        self.adversary: adversary_module.Adversary = None

        self.msg_store = simpy.Store(env)
        self.recv_messages_process = env.process(self.recv_messages())

    def __repr__(self):
        # return (
        #     "Server( \n"
        #     f"{super().__repr__()} \n"
        #     ")"
        # )
        return f"Server(id= {self._id})"

    def put(self, msg: message.Message):
        slog(DEBUG, self.env, self, "recved", msg=msg)

        # if self.adversary:
        #     self.adversary.server_recved_msg(server_id=self._id)

        self.msg_store.put(msg)

    def recv_messages(self):
        slog(DEBUG, self.env, self, "started")

        num_msgs_recved = 0
        while True:
            msg = yield self.msg_store.get()
            num_msgs_recved += 1
            slog(
                DEBUG, self.env, self,
                "processed",
                num_msgs_recved=num_msgs_recved,
                msg=msg,
            )

            if msg._type == message.MessageType.GET:
                for _ in range(msg.num_msgs_to_recv):
                    msg_ = message.DataMessage(
                        _id=self.num_msgs_sent,
                        src_id=msg.dst_id,
                        dst_id=msg.src_id,
                    )
                    self.next_hop.put(msg_)
                    slog(
                        DEBUG, self.env, self,
                        "sent",
                        num_msgs_sent=self.num_msgs_sent,
                        msg=msg_,
                    )

                    self.num_msgs_sent += 1

                    if self.adversary:
                        self.adversary.server_sent_msg(msg=msg_)

        slog(DEBUG, self.env, self, "done")
