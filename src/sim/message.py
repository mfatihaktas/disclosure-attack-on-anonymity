import enum


class MessageType(enum.Enum):
    DATA="DATA"
    GET="GET"
    POST="POST"


class Message:
    def __init__(
        self,
        _id: str,
        _type: MessageType,
        src_id: int,
        dst_id: int,
    ):
        self._id = _id
        self._type = _type
        self.src_id = src_id
        self.dst_id = dst_id

    def __repr__(self):
        return (
            "Message( \n"
            f"\t id= {self._id} \n"
            f"\t type= {self._type} \n"
            f"\t src_id= {self.src_id} \n"
            f"\t dst_id= {self.dst_id} \n"
            ")"
        )
        # return f"Message(id= {self._id})"


class GetRequest(Message):
    def __init__(
        self,
        _id: str,
        src_id: int,
        dst_id: int,
        num_msgs_to_recv: int,
    ):
        super().__init__(
            _id=_id,
            _type=MessageType.GET,
            src_id=src_id,
            dst_id=dst_id,
        )
        self.num_msgs_to_recv = num_msgs_to_recv


class DataMessage(Message):
    def __init__(
        self,
        _id: str,
        src_id: int,
        dst_id: int,
    ):
        super().__init__(
            _id=_id,
            _type=MessageType.DATA,
            src_id=src_id,
            dst_id=dst_id,
        )
