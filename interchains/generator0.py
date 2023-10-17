from operator import index
import random
# import copy
# import json
# import os

import itypes as it
from config import config 

def get_ruler(r, p):
    ruler = []
    for i in range(r):
        l = p // r + (1 if r - i <= p % r else 0)
        ruler.append(l)
    return ruler

class Generator:

    def __init__(self, config_generator) -> None: # 第二个参数无用 为了interchains中兼容
        self.parachain_number = config["parachain_number"]
        self.relaychain_number = config["relaychain_number"]
        self.crosschain_rate = 0.047 # 当做0.05
        self.logic_tx_id = 0
        self.write_to_file = False # 为了interchains中兼容
    
    def write_txs(self):
        pass

    def generate_txs(self, timestamp):
        logic_txs_send_rate = 2000 + (timestamp // 12) * 100 # 2000 3900 5100 6700 8400 # 1800 2500 3500 4500
        txs = []
        for i in range(logic_txs_send_rate):
            logic_tx = self.generate_tx(timestamp)
            txs.append(logic_tx)
            self.logic_tx_id += 1
        return txs, logic_txs_send_rate

    def generate_tx(self, timestamp):
        r1 = random.randint(0, self.parachain_number - 1)
        source_chain_id = 1000 + r1
        r2 = random.random()
        if r2 > self.crosschain_rate:
            dest_chain_id = source_chain_id
        else:
            r3 = r1
            while r3 == r1:
                r3 = random.randint(0, self.parachain_number - 1)
            dest_chain_id = 1000 + r3
        return it.LogicTx(self.logic_tx_id, source_chain_id, dest_chain_id, timestamp)

    # def generate_txs(self, timestamp):
    #     actual_parachain_number = 84 + (timestamp // 12) # 5 39 51 67 84
    #     if (timestamp % 6) == 0:
    #         print(actual_parachain_number)
    #     logic_txs_send_rate = 100 * actual_parachain_number

    #     parachain_ruler = get_ruler(self.relaychain_number, self.parachain_number)
    #     actual_parachain_ruler = get_ruler(self.relaychain_number, actual_parachain_number)
    #     actual_parachain_list = []
    #     for i in range(self.relaychain_number):
    #         for j in range(actual_parachain_ruler[i]):
    #             actual_parachain_list.append(sum(parachain_ruler[:i]) + j)
    #     # print(actual_parachain_list)

    #     txs = []
    #     for i in range(logic_txs_send_rate):
    #         logic_tx = self.generate_tx(timestamp, actual_parachain_number, actual_parachain_list)
    #         txs.append(logic_tx)
    #         self.logic_tx_id += 1
    #     return txs, logic_txs_send_rate

    # def generate_tx(self, timestamp, actual_parachain_number, actual_parachain_list):
    #     r1 = random.randint(0, actual_parachain_number - 1)
    #     source_chain_id = 1000 + actual_parachain_list[r1]
    #     r2 = random.random()
    #     if r2 > self.crosschain_rate:
    #         dest_chain_id = source_chain_id
    #     else:
    #         r3 = r1
    #         while r3 == r1:
    #             r3 = random.randint(0, actual_parachain_number - 1)
    #         dest_chain_id = 1000 + actual_parachain_list[r3]
    #     return it.LogicTx(self.logic_tx_id, source_chain_id, dest_chain_id, timestamp)

if __name__ == '__main__':
    # print(config_generator)
    g = Generator(config)
    # for i in range(600):
    #     g.generate_txs(i)

    g.generate_txs(12)
    print(g.logic_tx_id)


# relay_num
# relay_num, actual_parachain_number -> actual_parachain_list 两次ruler加一个循环装进列表
# random.randint(0, actual_parachain_number-1) -> index
# actual_parachain_list, index -> source/dest