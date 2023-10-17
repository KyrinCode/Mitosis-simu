import collections
import logging
import copy
import numpy as np
import json

import itypes as it
from generator0 import Generator
from config import config, config_generator

# logging config
logging.basicConfig(
    level = logging.INFO,                 
    format = "%(asctime)s %(levelname)s %(message)s ",
    datefmt = '[%d] %H:%M:%S'
)

# performance
timestamp = []
send_rate = []
# parachain_number = []
max_ratio = []
tps = []
delays = {}
avg_delay = []
crosschain_delays = {}
avg_crosschain_delay = []

class InterChains:

    timestamp = 0

    logic_txs_cnt = 0
    logic_txs_sent = [] # value
    logic_txs_done = [] # id

    actual_txs_cnt = 0
    actual_txs = [] # value

    blocks_cnt = 0
    blocks = [] # value

    chains = {} # parachain | relaychain

    topology = {} # 每条链的上下级字典
    
    def __init__(self, config) -> None:
        self.init_config(config)
        self.init_status()
        
        self.init_topology()
        self.init_parachains()
        self.init_relaychains()

        self.generator = Generator(config_generator)

        # self.print_status()

    def init_config(self, config):
        self.parachain_number = config["parachain_number"]
        self.relaychain_number = config["relaychain_number"]
        self.parachain_block_size = config["parachain_block_size"]
        self.relaychain_block_size = config["relaychain_block_size"]
        self.heartbeat = config["heartbeat"]
        self.logic_txs_total = config["logic_txs_total"]
        self.topology_config = config["topology"]

    def init_status(self):
        self.timestamp = 0
        self.logic_txs_cnt = 0
        self.logic_txs_sent = []
        self.logic_txs_done = []
        self.actual_txs_cnt = 0
        self.actual_txs = []
        self.blocks_cnt = 0
        self.blocks = []
        self.chains = {}
        self.topology = {}

    def init_parachains(self):
        # parachain id start from 1000
        for id in range(1000, 1000 + self.parachain_number):
            parachain = it.Chain(id, 0, self.parachain_block_size)
            self.chains[id] = parachain
            # logging.info
    
    def init_relaychains(self):
        # relaychain id start from 0
        for id in range(0, self.relaychain_number):
            relaychain = it.Chain(id, 1, self.relaychain_block_size)
            self.chains[id] = relaychain
            # logging.info

    def init_topology(self):
        for k, v in self.topology_config["one-many"].items():
            self.topology[k] = v[:]
            for id in v:
                self.topology[id] = k
        for i in self.topology_config["many-many"]:
            for j in self.topology_config["many-many"]:
                if j != i:
                    self.topology[i].append(j)

    def print_status(self):
        print("------------------ config ------------------")
        print("parachain_number: ", self.parachain_number)
        print("relaychain_number: ", self.relaychain_number)
        print("parachain_block_size: ", self.parachain_block_size)
        print("relaychain_block_size: ", self.relaychain_block_size)
        print("heartbeat: ", self.heartbeat)
        print("logic_txs_total: ", self.logic_txs_total)
        print("topology_config: ", self.topology_config)
        print("topology: ", self.topology)
        
        print("------------------ status ------------------")

        print("timestamp: ", self.timestamp)

        print("logic_txs_cnt: ", self.logic_txs_cnt)
        # print("logic_txs_sent: ", self.logic_txs_sent) # [] # value
        print("logic_txs_done: ", self.logic_txs_done) # [] # id

        print("actual_txs_cnt: ", self.actual_txs_cnt)
        # print("actual_txs: ", self.actual_txs) # [] # value

        print("blocks_cnt: ", self.blocks_cnt)
        # print("blocks: ", self.blocks) # [] # value

        print("chains: ", self.chains) # {} # parachain | relaychain
        print("--------------------------------------------")

    def get_next_hop(self, sender_chain_id, dest_chain_id): # 通过 self.topology 递归找到交易下一跳
        if sender_chain_id == dest_chain_id:
            return -1 # 最后一跳结束返回 -1
        if sender_chain_id >= 1000: # 源链
            return self.topology[sender_chain_id]
        elif sender_chain_id == self.topology[dest_chain_id]: # 目的链归属当前中继
            return dest_chain_id
        else: # 目的链归属其他中继
            return self.topology[dest_chain_id]

    def is_done(self) -> bool:
        if len(self.logic_txs_done) >= self.logic_txs_total:
            return True

    def send_txs(self):
        # generate logic txs
        if self.logic_txs_cnt >= self.logic_txs_total:
            self.logic_txs_total = self.logic_txs_cnt
            return
        # logic_txs, num = Generator(self.parachain_number, self.timestamp, self.logic_txs_cnt).generate_txs()
        logic_txs, num = self.generator.generate_txs(self.timestamp)
        self.logic_txs_cnt += num
        
        # calculate corresponding actual txs
        for logic_tx in logic_txs:
            # record sent logic txs
            logic_tx_id = logic_tx.id
            self.logic_txs_sent.append(logic_tx)
            sender_chain_id = self.logic_txs_sent[logic_tx_id].source_chain_id
            dest_chain_id = self.logic_txs_sent[logic_tx_id].dest_chain_id
            hop_id = 0
            
            while(1):
                next_chain_id = self.get_next_hop(sender_chain_id, dest_chain_id)
                # print(next_chain_id, next_chain_type)
                actual_tx = it.ActualTx(self.actual_txs_cnt, logic_tx_id, hop_id, sender_chain_id, next_chain_id)
                self.actual_txs_cnt += 1
                self.actual_txs.append(actual_tx)

                self.logic_txs_sent[logic_tx_id].actual_tx_ids.append(actual_tx.id)
                
                if next_chain_id == -1:
                    break
                else:
                    sender_chain_id = next_chain_id
                    hop_id += 1
            self.logic_txs_sent[logic_tx_id].hops = hop_id
                        
            # send 1st actual tx to corresponding chain's txpool
            first_actual_tx = self.actual_txs[self.logic_txs_sent[logic_tx_id].actual_tx_ids[0]]
            first_actual_tx.send_timestamp = self.timestamp
            self.chains[first_actual_tx.this_chain_id].txpool.append(first_actual_tx.id)

            # for id in range(1000, 1000 + self.parachain_number):
            #     print("chainid", id)
            #     for i in range(0, len(self.chains[id].txpool)):
            #         print(self.chains[id].txpool[i])

    def prepare_block(self):
        # print("prepare_block")
        for chain_id, chain in self.chains.items():
            # sort txpool with rule: send timestamp > logic tx id
            # chain.sort_txpool()
            # chain.txpool = sorted(chain.txpool, key=lambda i: (self.actual_txs[i].send_timestamp, self.actual_txs[i].logic_tx_id))
            # pack actual txs from txpool
            packed_txs = []
            # for i in range(0, len(chain.txpool)):
            #     print(chain.txpool[i])
            for i in range(0, chain.block_size):
                try:
                    
                    actual_tx_id = chain.txpool.popleft()
                    
                    # 测试是否是引用 actual_tx 原始位置是否变化
                    # self.logic_tx_sent[tx.logic_tx_id].actual_txs[tx.hop_id].timestamps.append(self.timestamp)
                    # self.logic_tx_sent[tx.logic_tx_id].actual_txs[tx.hop_id].block_height = len(chain.blocks)
                    actual_tx = self.actual_txs[actual_tx_id]
                    actual_tx.process_timestamp = self.timestamp
                    actual_tx.block_height = len(chain.blocks)
                    packed_txs.append(actual_tx_id)
                except Exception as ex:
                    break
            block = it.Block(
                self.blocks_cnt,
                chain_id,
                len(chain.blocks),
                self.timestamp,
                packed_txs
            )
            # print(packed_txs)
            # append block to chain
            self.blocks.append(block)
            self.chains[chain_id].blocks.append(self.blocks_cnt)
            self.blocks_cnt += 1

    def process_block(self):
        # print("process_block")
        for chain_id, chain in self.chains.items():
            latest_block_id = chain.blocks[-1]
            # print(latest_block_id)
            latest_block = self.blocks[latest_block_id]
            # print(latest_block)
            for actual_tx_id in latest_block.txs:
                # print("actual_tx_id: ", actual_tx_id)
                actual_tx = self.actual_txs[actual_tx_id]
                actual_tx.is_done = True
                logic_tx = self.logic_txs_sent[actual_tx.logic_tx_id]                    
                # get next hop actual tx if exists and send to corresponding chain's txpool
                try:
                    next_actual_tx_id = logic_tx.actual_tx_ids[actual_tx.hop_id + 1]  
                    next_actual_tx = self.actual_txs[next_actual_tx_id]
                    next_actual_tx.send_timestamp = self.timestamp # 需要测试是否实际交易原始位置也有了timestamps[0]
                    self.chains[next_actual_tx.this_chain_id].txpool.append(next_actual_tx_id)
                except Exception as ex:
                    # update corresponding logic tx state
                    logic_tx.finish_timestamp = actual_tx.process_timestamp
                    logic_tx.is_done = True
                    self.logic_txs_done.append(logic_tx.id)
                    # print(logic_tx)

    def calculate_load(self, log=False):
        print('\n')
        ratios = []
        for k, v in self.topology_config["one-many"].items():
            # print(k)
            # print(len(self.chains[k].txpool))
            relaychain_ratio = len(self.chains[k].txpool) / self.chains[k].block_size
            if log: logging.info("Relaychain %s load ratio: %.2f" % (k, relaychain_ratio))
            ratios.append(relaychain_ratio)
            for id in v:
                if id >= 1000:
                    parachain_ratio = len(self.chains[id].txpool) / self.chains[id].block_size
                    if log: logging.info("Parachain %s load ratio: %.2f" % (id, parachain_ratio))
        Avg = np.mean(ratios)
        if log: logging.info("Average of ratios: %.4f" % (Avg))
        Var = np.var(ratios)
        if log: logging.info("Variance of ratios: %.4f" % (Var))
        Max = max(ratios)
        if log: logging.info("Max of ratios: %.4f" % (Max))
        return ratios, Avg, Var, Max

    def calculate_tps_delay(self):
        last_id = len(self.logic_txs_done) - 1
        logic_tps = 0
        logic_delay = []
        logic_crosschain_delay = []
        while last_id >= 0 and self.logic_txs_sent[self.logic_txs_done[last_id]].finish_timestamp == self.timestamp:
            logic_tps += 1
            delay = self.logic_txs_sent[self.logic_txs_done[last_id]].finish_timestamp - self.logic_txs_sent[self.logic_txs_done[last_id]].send_timestamp
            logic_delay.append(delay)
            if self.logic_txs_sent[self.logic_txs_done[last_id]].source_chain_id != self.logic_txs_sent[self.logic_txs_done[last_id]].dest_chain_id:
                logic_crosschain_delay.append(delay)
            last_id -= 1
        logic_tps /= config["heartbeat"]
        logic_delay_avg = np.mean(logic_delay)
        logic_crosschain_delay_avg = np.mean(logic_crosschain_delay)
        # logic_delay_max = max(logic_delay)
        logging.info("Timestamp: %d" % (self.timestamp))
        timestamp.append(self.timestamp + 1)
        s_rate = 2000 + (self.timestamp // 12) * 100
        send_rate.append(s_rate)
        # p_num = 84 + (self.timestamp // 12)
        # parachain_number.append(p_num)
        logging.info("TPS: %.4f" % (logic_tps))
        tps.append(logic_tps)

        delays[s_rate] = logic_delay
        crosschain_delays[s_rate] = logic_crosschain_delay
        # delays[p_num] = logic_delay
        # crosschain_delays[p_num] = logic_crosschain_delay

        logging.info("Average of delay: %.4f" % (logic_delay_avg))
        avg_delay.append(logic_delay_avg)
        # logging.info("Max of delay: %.4f" % (logic_delay_max))
        logging.info("Average of crosschain delay: %.4f" % (logic_crosschain_delay_avg))
        avg_crosschain_delay.append(logic_crosschain_delay_avg)

    def simulation(self, block_height=None): # 分片算法时通过采样时刻计算负载
        while self.is_done() != True and (block_height == None or block_height > 0):
            self.send_txs()

            if self.timestamp % self.heartbeat == self.heartbeat - 1:
                # self.calculate_load()
                if block_height != None and block_height > 0:
                    block_height -= 1
                if block_height == None:
                    _, _, _, Max = self.calculate_load()
                    if Max >= 1.2:
                        return self.calculate_load(True)
                elif block_height == -1:
                    if self.generator.write_to_file:
                        self.generator.write_txs()
                    return self.calculate_load(True) # 计算打包第block_height前的load

                _, _, _, M = self.calculate_load()
                max_ratio.append(M)

                self.prepare_block()

                self.process_block()
                if self.timestamp % (self.heartbeat * 2) == self.heartbeat * 2 - 1:
                    self.calculate_tps_delay()

                # track_id = 59
                # try:
                #     print("---------------")
                #     # print(len(self.logic_txs_sent))
                #     # print(len(self.logic_txs_done))
                #     # for i in range(0, len(self.logic_txs_sent)):
                #     #     print(self.logic_txs_sent[i])
                #     print(self.logic_txs_done)
                #     print(self.logic_txs_sent[track_id])
                    
                #     for i in range(0, self.actual_txs_cnt):
                #         if self.actual_txs[i].logic_tx_id == track_id:
                #             print(self.actual_txs[i])
                #     print("---------------")
                # except Exception as ex:
                #     pass
                # for id in range(1000, 999 + self.parachain_number):
                #     print(len(self.chains[id].txpool))

            self.timestamp += 1

def load_sharding():
    with open("sharding.json", "r") as json_file:
        f = json.load(json_file)

    config_1 = copy.deepcopy(config)
    config_1["topology"]["one-many"][0] = [i for i in range(1000, 1100)]
    config_1["topology"]["many-many"] = [0]

    config_2 = copy.deepcopy(config)
    config_2["topology"]["one-many"][0] = [i for i in range(1000, 1050)]
    config_2["topology"]["one-many"][1] = [i for i in range(1050, 1100)]
    config_2["topology"]["many-many"] = [0, 1]

    config_3 = copy.deepcopy(config)
    config_3["topology"]["one-many"][0] = [i for i in range(1000, 1033)]
    config_3["topology"]["one-many"][1] = [i for i in range(1033, 1066)]
    config_3["topology"]["one-many"][2] = [i for i in range(1066, 1100)]
    config_3["topology"]["many-many"] = [0, 1, 2]

    config_4 = copy.deepcopy(config)
    config_4["topology"]["one-many"][0] = [i for i in range(1000, 1025)]
    config_4["topology"]["one-many"][1] = [i for i in range(1025, 1050)]
    config_4["topology"]["one-many"][2] = [i for i in range(1050, 1075)]
    config_4["topology"]["one-many"][3] = [i for i in range(1075, 1100)]
    config_4["topology"]["many-many"] = [0, 1, 2, 3]

    config_5 = copy.deepcopy(config)
    config_5["topology"]["one-many"][0] = [i for i in range(1000, 1020)]
    config_5["topology"]["one-many"][1] = [i for i in range(1020, 1040)]
    config_5["topology"]["one-many"][2] = [i for i in range(1040, 1060)]
    config_5["topology"]["one-many"][3] = [i for i in range(1060, 1080)]
    config_5["topology"]["one-many"][4] = [i for i in range(1080, 1100)]
    config_5["topology"]["many-many"] = [0, 1, 2, 3, 4]

    config_10 = copy.deepcopy(config)
    config_10["topology"]["one-many"][0] = [i for i in range(1000, 1010)]
    config_10["topology"]["one-many"][1] = [i for i in range(1010, 1020)]
    config_10["topology"]["one-many"][2] = [i for i in range(1020, 1030)]
    config_10["topology"]["one-many"][3] = [i for i in range(1030, 1040)]
    config_10["topology"]["one-many"][4] = [i for i in range(1040, 1050)]
    config_10["topology"]["one-many"][5] = [i for i in range(1050, 1060)]
    config_10["topology"]["one-many"][6] = [i for i in range(1060, 1070)]
    config_10["topology"]["one-many"][7] = [i for i in range(1070, 1080)]
    config_10["topology"]["one-many"][8] = [i for i in range(1080, 1090)]
    config_10["topology"]["one-many"][9] = [i for i in range(1090, 1100)]
    config_10["topology"]["many-many"] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    config_ga = copy.deepcopy(config)
    # for i in range(config_ga["relaychain_number"]):
    #     config_ga["topology"]["one-many"][i] = f["ga"][str(config_ga["relaychain_number"]) + "relays"][i]
    # config_ga["topology"]["many-many"] = [i for i in range(config_ga["relaychain_number"])]

    config_ldg = copy.deepcopy(config)
    # for i in range(config_ldg["relaychain_number"]):
    #     config_ldg["topology"]["one-many"][i] = f["ldg"][str(config_ldg["relaychain_number"]) + "relays"][i]
    # config_ldg["topology"]["many-many"] = [i for i in range(config_ldg["relaychain_number"])]

    config_metis = copy.deepcopy(config)
    # for i in range(config_metis["relaychain_number"]):
    #     config_metis["topology"]["one-many"][i] = f["metis"][str(config_metis["relaychain_number"]) + "relays"][i]
    # config_metis["topology"]["many-many"] = [i for i in range(config_metis["relaychain_number"])]

    return config_1, config_2, config_3, config_4, config_5, config_10, config_ga, config_metis, config_ldg

if __name__ == '__main__':

    config_1, config_2, config_3, config_4, config_5, config_10, config_ga, config_metis, config_ldg = load_sharding()
    simu_num = 162 # 34 # 192
    print("\n---- 1?relay -----")
    base = InterChains(config_1)
    base.simulation(simu_num)
    # print("\n------ GA -------")
    # ga = InterChains(config_ga)
    # ga.simulation(simu_num)
    # print("\n------ LDG ------")
    # ldg = InterChains(config_ldg)
    # ldg.simulation(simu_num)
    # print("\n----- METIS -----")
    # metis = InterChains(config_metis)
    # metis.simulation(simu_num)

    print(len(timestamp))
    print("timestamp =", timestamp)
    # print(len(send_rate))
    print("send_rate =", send_rate)
    # print(len(parachain_number))
    # print("parachain_number =", parachain_number)
    # print(len(max_ratio)//2)
    print("max_ratio =", [max_ratio[i*2+1] for i in range(len(max_ratio)//2)])
    # print(len(tps))
    print("tps =", tps)
    # print(len(avg_delay))
    print("avg_delay =", avg_delay)
    # print(len(avg_crosschain_delay))
    print("avg_crosschain_delay =", avg_crosschain_delay)

    with open("delays_2000_10000.json", "w") as json_file:
        json_file.write(json.dumps(delays, indent=4))
    with open("crosschain_delays_2000_10000.json", "w") as json_file:
        json_file.write(json.dumps(crosschain_delays, indent=4))

    