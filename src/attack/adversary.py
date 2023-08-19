import abc
import simpy

from src.sim import message


class Adversary(abc.ABC):
    def __init__(
        self,
        env: simpy.Environment,
    ):
        self.env = env

    # @abc.abstractmethod
    # def client_sent_msg(self, msg: message.Message):
    #     pass

    @abc.abstractmethod
    def client_completed_get_request(self, num_msgs_recved_for_get_request: int):
        pass

    # @abc.abstractmethod
    # def server_recved_msg(self, msg: message.Message):
    #     pass

    @abc.abstractmethod
    def server_sent_msg(self, msg: message.Message):
        pass
