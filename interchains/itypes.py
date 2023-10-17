import collections
from time import process_time


class Chain:
    id = 0
    chain_type = 0 # 0 parachain 1 relaychain
    block_size = 0
    txpool = collections.deque([]) # 本链将发出的 + 其他链发来的 | sort: send timestamp > logic_tx_id
    blocks = []

    def __init__(self, _id, _chain_type, _block_size) -> None:
        self.id = _id
        self.chain_type = _chain_type
        self.block_size = _block_size
        self.txpool = collections.deque([])
        self.blocks = []

    def __str__(self) -> str:
        return str(self.__dict__)

    def sort_txpool(self):
        pass

class Block:
    id = 0
    chain_id = 0
    block_height = 0
    timestamp = 0
    txs = []

    def __init__(self, _id, _chain_id, _block_height, _timestamp, _txs) -> None:
        self.id = _id
        self.chain_id = _chain_id
        self.block_height = _block_height
        self.timestamp = _timestamp
        self.txs = _txs[:]

    def __str__(self) -> str:
        return str(self.__dict__)

class LogicTx:
    id = 0
    source_chain_id = 0
    dest_chain_id = 0
    hops = 0
    is_done = False
    send_timestamp = 0
    finish_timestamp = 0
    actual_tx_ids = []

    def __init__(self, _id, _source_chain_id, _dest_chain_id, _timestamp) -> None:
        self.id = _id
        self.source_chain_id = _source_chain_id
        self.dest_chain_id = _dest_chain_id
        self.send_timestamp = _timestamp
        self.is_done = False
        self.actual_tx_ids = []

    def __str__(self) -> str:
        
        # res = str(self.__dict__)[:-1] + \
        # (", 'hops': %d" % self.hops) + \
        # (", 'is_done': %s" % self.is_done) + \
        # (", 'send_timestamp': %s" % self.send_timestamp) + \
        # (", 'process_timestamp': %s" % self.process_timestamp) + \
        # (", 'actual_txs': ")
        # for i in self.actual_tx_ids:
        #     res += i.__str__()
        # res += "}"
        return str(self.__dict__)

class ActualTx:
    id = 0
    logic_tx_id = 0
    hop_id = 0
    this_chain_id = 0
    next_chain_id = 0
    block_height = 0
    is_done = False
    send_timestamp = 0
    process_timestamp = 0 # block timestamp

    def __init__(self, _id, _logic_tx_id, _hop_id, _this_chain_id, _next_chain_id) -> None:
        self.id = _id
        self.logic_tx_id = _logic_tx_id
        self.hop_id = _hop_id
        self.this_chain_id = _this_chain_id
        self.next_chain_id = _next_chain_id
        self.is_done = False

    def __str__(self) -> str:
        # return str(self.__dict__)[:-1] + (", 'block_height': %d" % self.block_height) + (", 'send_timestamp': %d" % self.send_timestamp) + (", 'process_timestamp': %d" % self.process_timestamp) + "}"
        return str(self.__dict__)