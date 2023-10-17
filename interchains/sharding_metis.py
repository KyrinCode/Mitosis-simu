import networkx as nx
import nxmetis
import json
import copy

from interchains import InterChains
from generator import Generator
from config import config, config_generator

class METIS:

    def __init__(self, simu_num) -> None:
        self.simu_num = simu_num
        self.parachain_number = config["parachain_number"]
        self.relaychain_number = config["relaychain_number"]
        self.logic_txs_cnt = 0
        self.generator = Generator(config_generator)
        self.init_adj()
        self.partition = [[] for i in range(self.relaychain_number)]
        pass

    def init_adj(self):
        self.adj = [[0 for i in range(self.parachain_number)] for i in range(self.parachain_number)]
        for i in range(self.simu_num):
            logic_txs, num = self.generator.generate_txs(i)
            for logic_tx in logic_txs:
                self.adj[logic_tx.source_chain_id - 1000][logic_tx.dest_chain_id - 1000] += 1
            self.logic_txs_cnt += num

    def metis(self):
        G = nx.Graph()
        for i in range(self.parachain_number):
            for j in range(i, self.parachain_number):
                if i == j:
                    pass
                    # node weight
                else:
                    w = self.adj[i][j] + self.adj[j][i]
                    if w > 0:
                        G.add_edge(i + 1000, j + 1000, weight=w)

        _, self.partition = nxmetis.partition(G, self.relaychain_number)
        l = len([i for j in self.partition for i in j])
        return l

    def correct_min(self):
        ruler = []
        for i in range(self.relaychain_number):
            l = self.parachain_number // self.relaychain_number + (1 if self.relaychain_number - i <= self.parachain_number % self.relaychain_number else 0)
            ruler.append(l)

        while 1:
            # 升序排序各中继的平行链数量
            self.partition.sort(key = lambda x : len(x))
            if len(self.partition[0]) == ruler[0]:
                break
            
            chain = self.partition[self.relaychain_number - 1][0] # 找出最后中继中跨片交易最少的平行链
            volumes = [0 for _ in range(self.parachain_number)]
            for i in self.partition[self.relaychain_number - 1]:
                for j in range(self.parachain_number):
                    if i - 1000 != j:
                        volumes[i - 1000] += (self.adj[i - 1000][j] + self.adj[j][i - 1000])
                if volumes[i - 1000] < volumes[chain - 1000]:
                    chain = i
            
            dest_relay = 0 # 找出未达到平行链数量要求的中继中与该平行链交互最多的中继
            volumes = [0 for _ in range(self.relaychain_number - 1)]
            for k in range(self.relaychain_number - 1):
                if len(self.partition[k]) >= ruler[k]:
                    break
                for i in self.partition[k]:
                    volumes[k] += self.adj[chain - 1000][i - 1000] + self.adj[i - 1000][chain - 1000]
                if volumes[k] > volumes[dest_relay]:
                    dest_relay = k
            
            self.partition[self.relaychain_number - 1].remove(chain)
            self.partition[dest_relay].append(chain)

    def correct_max(self):
        ruler = []
        for i in range(self.relaychain_number):
            l = self.parachain_number // self.relaychain_number + (1 if self.relaychain_number - i <= self.parachain_number % self.relaychain_number else 0)
            ruler.append(l)

        while 1:
            # 升序排序各中继的平行链数量
            self.partition.sort(key = lambda x : len(x))
            # if len(self.partition[relaychain_number - 1]) == ruler[relaychain_number - 1]:
            if len(self.partition[0]) == ruler[0]:
                break
            
            chain = 0 # 找出最后中继中跨中继占比最高的平行链
            rate = 0
            volumes = []
            for i in self.partition[self.relaychain_number - 1]:
                tmp_volumes = [0 for _ in range(self.relaychain_number)]
                for j in range(self.parachain_number):
                    for k in range(self.relaychain_number):
                        if j + 1000 in self.partition[k]:
                            tmp_volumes[k] += (self.adj[i - 1000][j] + self.adj[j][i - 1000])
                tmp_rate = (sum(tmp_volumes) - tmp_volumes[self.relaychain_number - 1]) / sum(tmp_volumes)
                if tmp_rate > rate:
                    chain = i
                    rate = tmp_rate
                    volumes = copy.deepcopy(tmp_volumes)
            
            dest_relay = 0 # 找出未达到平行链数量要求的中继中与该平行链交互最多的中继
            vol = volumes[0]
            for i in range(1, self.relaychain_number):
                if len(self.partition[i]) >= ruler[i]:
                    break
                if volumes[i] > vol:
                    dest_relay = i
                    vol = volumes[i]
            
            self.partition[self.relaychain_number - 1].remove(chain)
            self.partition[dest_relay].append(chain)

    def fitness(self): # 令最高占比最小
        parachain_list = [i for j in self.partition for i in j]
        print(parachain_list)
        tmp_config = copy.deepcopy(config)
        pos = 0
        for i in range(self.relaychain_number):
            l = self.parachain_number // self.relaychain_number + (1 if self.relaychain_number - i <= self.parachain_number % self.relaychain_number else 0)
            tmp = []
            for j in range(l):
                tmp.append(parachain_list[pos])
                pos += 1
            tmp_config["topology"]["one-many"][i] = tmp
        tmp_config["topology"]["many-many"] = [i for i in range(self.relaychain_number)]
        print(tmp_config)
        interchains = InterChains(tmp_config)
        _, _, _, Max = interchains.simulation(10)
        return Max
    
    def save_result(self):
        with open("sharding.json", "r") as json_file:
            f = json.load(json_file)
        f["metis"][str(self.relaychain_number) + "relays"] = self.partition
        with open("sharding.json", "w") as json_file:
            json_file.write(json.dumps(f, indent=4))

    def main(self):
        l = self.metis()
        if l == self.parachain_number:
            self.correct_max()
        Max = self.fitness()
        self.save_result()
        return Max

# res = [i for j in parts for i in j]

if __name__ == '__main__':
    simu_num = 100
    metis = METIS(simu_num)
    Max = metis.main()
    print(metis.partition)
    print(Max)

# while:
#     升序排序各中继的平行链数量
#     if 最后中继的平行链数量已达到要求:
#         return 方案
#     找出最后中继中（中继内/中继间）最低的平行链
#     找出未达到平行链数量要求的中继中与该平行链交互最多的中继
#     修改方案，将该平行链转移