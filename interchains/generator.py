import random
import copy
import json
import os

import itypes as it
from config import config, config_data, config_generator

def weights2roulette(weights):
    roulette = copy.deepcopy(weights)
    roulette[-1] = 1 - roulette[-1]
    for i in range(len(weights) - 2, -1, -1):
        roulette[i] = roulette[i + 1] - roulette[i]
    return roulette

def get_id_from_roulette(n, arr, l, r):
    if r - l + 1 == 2:
        return l
    m = l + (r - l) // 2
    if arr[m] > n:
        return get_id_from_roulette(n, arr, l, m)
    else:
        return get_id_from_roulette(n, arr, m, r)

class Generator:

    def __init__(self, config_generator) -> None:
        self.parachain_number = len(config_generator["parachain_weights"])
        self.parachain_roulette = weights2roulette(config_generator["parachain_weights"])
        self.parachain_crosschain_rates = config_generator["parachain_crosschain_rates"]
        # self.parachain_crosschain_roulette = self.weights2roulette(config_generator["parachain_crosschain_weights"])
        self.parachain_crosschain_roulette = {}
        for i in range(self.parachain_number):
            self.parachain_crosschain_roulette[i] = weights2roulette(config_generator["parachain_connection_weights"][i])
        # self.timestamp = 0
        self.logic_tx_id = 0

        self.read_from_file = config_generator["read_from_file"]
        if self.read_from_file:
            self.txs_file = self.read_txs()
        self.write_to_file = config_generator["write_to_file"]
        if self.write_to_file:
            self.txs_file = self.read_txs()

    # def weights2roulette(self, weights):
    #     roulette = copy.deepcopy(weights)
    #     roulette[-1] = 1 - roulette[-1]
    #     for i in range(self.parachain_number - 2, -1, -1):
    #         roulette[i] = roulette[i + 1] - roulette[i]
    #     return roulette

    # def get_id_from_roulette(self, n, arr, l, r):
    #     if r - l + 1 == 2:
    #         return l
    #     m = l + (r - l) // 2
    #     if arr[m] > n:
    #         return self.get_id_from_roulette(n, arr, l, m)
    #     else:
    #         return self.get_id_from_roulette(n, arr, m, r)

    def read_txs(self):
        with open("generated_txs.json", "r") as json_file:
            f = json.load(json_file)
        return f

    def write_txs(self):
        with open("generated_txs.json", "w") as json_file:
            json_file.write(json.dumps(self.txs_file, indent=4))

    # 每一轮中逐档提升交易发送速度直到达到某中继瓶颈
    # 单中继一轮（达到单中继瓶颈） | 中继分片生成新拓扑 -> 多中继一轮（比较中继分片前后以及分片策略的均衡通量时延）
    # 添加更多业务链 -> 多中继一轮（达到某中继瓶颈） | 中继分片形成新拓扑 -> 多中继一轮（验证动态中继分片）
    def generate_txs(self, timestamp):
        if self.read_from_file:
            txs_file = self.txs_file[str(timestamp)]
            # 1relays瓶颈为 1700
            # 2relays瓶颈分别为 2400 2300 (0.9140)
            # 3relays瓶颈分别为 3100 (0.8140) (1.6860)
            # 4relays瓶颈分别为 4500 4000 1800
            # 5relays瓶颈分别为 ok (0.8950) (0.8640)
            # 6relays瓶颈分别为 - ok ok
            logic_txs_send_rate = 1800 + (timestamp // 12) * 100 # len(txs_file)
            txs = []
            for i in range(logic_txs_send_rate):
                logic_tx = it.LogicTx(self.logic_tx_id, txs_file[i]["source_chain_id"], txs_file[i]["dest_chain_id"], txs_file[i]["send_timestamp"])
                txs.append(logic_tx)
                self.logic_tx_id += 1
        else:
            if self.logic_tx_id >= 0: # 随着交易数量增长加快交易发送速率
                logic_txs_send_rate = 5000
            txs = []
            for i in range(logic_txs_send_rate):
                logic_tx = self.generate_tx(timestamp)
                
                # 平行链发送交易数量限制
                logic_tx_number = [0 for _ in range(config["parachain_number"])]
                while logic_tx_number[logic_tx.source_chain_id - 1000] == config["parachain_block_size"]:
                    logic_tx = self.generate_tx(timestamp)
                logic_tx_number[logic_tx.source_chain_id - 1000] += 1

                txs.append(logic_tx)
                self.logic_tx_id += 1

            if self.write_to_file:
                txs_file = []
                for i in range(logic_txs_send_rate):
                    logic_tx_file = {}
                    logic_tx_file["id"] = txs[i].id
                    logic_tx_file["source_chain_id"] = txs[i].source_chain_id
                    logic_tx_file["dest_chain_id"] = txs[i].dest_chain_id
                    logic_tx_file["send_timestamp"] = txs[i].send_timestamp
                    txs_file.append(logic_tx_file)
                self.txs_file[str(timestamp)] = txs_file
        return txs, logic_txs_send_rate

    # connect with most parachains 5(4+25+40): stable coin issue, common good bridge/oracle
    # connect with many parachains 25(5+15+5): popular dapp defi/nft market
    # connect with limited parachains 70(3+2+1): self-reliant gamefi/metaverse/business
    def generate_tx(self, timestamp):
        r1 = random.random()
        source_chain_id = 1000 + get_id_from_roulette(r1, self.parachain_roulette, 0, self.parachain_number)
        r2 = random.random()
        if r2 > self.parachain_crosschain_rates[source_chain_id - 1000]:
            dest_chain_id = source_chain_id
        else:
            r3 = random.random()
            dest_chain_id = 1000 + get_id_from_roulette(r3, self.parachain_crosschain_roulette[source_chain_id - 1000], 0, self.parachain_number)
        return it.LogicTx(self.logic_tx_id, source_chain_id, dest_chain_id, timestamp)

    # def generate_tx(self, timestamp):
    #     # 按照概率生成交易
    #     # source_chain_id = random.randint(1000, 999 + self.parachain_number)
    #     # dest_chain_id = random.randint(1000, 999 + self.parachain_number)
    #     r = random.random()
    #     if r < 0.25:
    #         source_chain_id = random.randint(1000, 1004)
    #         dest_chain_id = random.randint(1000, 1014)
    #     # elif r < 0.67:
    #     #     source_chain_id = random.randint(1004, 1005)
    #     #     dest_chain_id = random.randint(1004, 1009)
    #     else:
    #         source_chain_id = random.randint(1005, 1014)
    #         dest_chain_id = random.randint(1000, 1014)
    #     return it.LogicTx(self.logic_tx_id, source_chain_id, dest_chain_id, timestamp)

def generate_config_generator():
    parachain_weights_normalized = normalize(config_data["parachain_weights"])
    parachain_number = len(parachain_weights_normalized)
    parachain_crosschain_rates = [random.uniform(config_data["crosschain_rate_range"][0], config_data["crosschain_rate_range"][1]) for _ in range(parachain_number)]
    # manipulate first rate
    # parachain_crosschain_rates[0] = 0.15
    parachain_crosschain_weights_normalized = normalize([parachain_weights_normalized[i] * parachain_crosschain_rates[i] for i in range(parachain_number)])
    parachain_crosschain_roulette = weights2roulette(parachain_crosschain_weights_normalized)
    parachain_connection_number = [round((parachain_number * config_data["max_connection_rate"] - config_data["min_connection_number"]) * parachain_crosschain_weights_normalized[i] / max(parachain_crosschain_weights_normalized) + config_data["min_connection_number"]) for i in range(parachain_number)]
    parachain_connections = [set() for _ in range(parachain_number)]
    for i in range(parachain_number):
        while len(parachain_connections[i]) < parachain_connection_number[i]:
            to = get_id_from_roulette(random.random(), parachain_crosschain_roulette, 0, parachain_number)
            if to != i and len(parachain_connections[to]) < parachain_connection_number[to]:
                parachain_connections[i].add(to)
                parachain_connections[to].add(i)
    parachain_connection_weights_normalized = [[0 for _ in range(parachain_number)] for _ in range(parachain_number)]
    for i in range(parachain_number):
        parachain_connections_tmp = list(parachain_connections[i])
        parachain_connection_weights_normalized_tmp = normalize([parachain_crosschain_weights_normalized[x] for x in parachain_connections_tmp])
        for j in range(parachain_connection_number[i]):
            parachain_connection_weights_normalized[i][parachain_connections_tmp[j]] = parachain_connection_weights_normalized_tmp[j]
    config_generator_new = {"parachain_weights": parachain_weights_normalized, "parachain_crosschain_rates": parachain_crosschain_rates, "parachain_connection_weights": parachain_connection_weights_normalized}
    print(config_generator_new)

def normalize(l):
    s = sum(l)
    return [x / s for x in l]


if __name__ == '__main__':
    # print(config_generator)
    g = Generator(config_generator)
    for i in range(600):
        g.generate_txs(i)
    if g.write_to_file:
        g.write_txs()

    # g.generate_txs(0)
    # print(g.logic_tx_id)

    # generate_config_generator()
