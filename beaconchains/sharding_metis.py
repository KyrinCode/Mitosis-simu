import networkx as nx
import nxmetis
import json
import copy

from beaconchains import BeaconChains
from config import config, config_generator

class METIS:

    def __init__(self) -> None:
        self.parachain_number = config["parachain_number"]
        self.relaychain_number = config["relaychain_number"]
        self.connections = config_generator["parachain_connection_weights"]
        self.partition = [[] for i in range(self.relaychain_number)]

    def metis(self):
        G = nx.Graph()
        for i in range(self.parachain_number):
            for j in range(i, self.parachain_number):
                if i == j:
                    pass
                else:
                    if self.connections[i][j] != 0 and self.connections[j][i] != 0:
                        G.add_edge(i + 1000, j + 1000)

        _, self.partition = nxmetis.partition(G, self.relaychain_number)
        l = len([i for j in self.partition for i in j])
        return l

    def correct(self):
        ruler = []
        for i in range(self.relaychain_number):
            l = self.parachain_number // self.relaychain_number + (1 if self.relaychain_number - i <= self.parachain_number % self.relaychain_number else 0)
            ruler.append(l)

        while 1:
            # 升序排序各中继的平行链数量
            self.partition.sort(key = lambda x : len(x))
            if len(self.partition[0]) == ruler[0]:
                break
            
            chain = self.partition[self.relaychain_number - 1][0] # 找出最后中继中连接数量最大的平行链
            connection_number = 0
            for i in self.partition[self.relaychain_number - 1]:
                tmp = sum([i > 0 for i in self.connections[i - 1000]])
                if tmp > connection_number:
                    connection_number = tmp
                    chain = i
            
            dest_relay = 0 # 未达到平行链数量要求的中继中平行链最少的中继
            
            self.partition[self.relaychain_number - 1].remove(chain)
            self.partition[dest_relay].append(chain)

    def fitness(self): # 令总维护中继数最小
        parachain_list = [i for j in self.partition for i in j]
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
        beaconchains = BeaconChains(tmp_config)
        relays = beaconchains.get_total_relays()
        return relays
    
    def save_result(self):
        with open("sharding.json", "r") as json_file:
            f = json.load(json_file)
        f["metis"][str(self.relaychain_number) + "relays"] = self.partition
        with open("sharding.json", "w") as json_file:
            json_file.write(json.dumps(f, indent=4))

    def main(self):
        self.metis()
        self.correct()
        relays = self.fitness()
        self.save_result()
        return relays

if __name__ == '__main__':
    metis = METIS()
    relays = metis.main()
    print(metis.partition)
    print(relays)