import copy
import json
import random

from beaconchains import BeaconChains
from config import config, config_generator

class LDG:
    def __init__(self):
        self.parachain_number = config["parachain_number"]
        self.relaychain_number = config["relaychain_number"]
        self.connections = config_generator["parachain_connection_weights"]
        self.partition = [[] for i in range(self.relaychain_number)]

    def get_capacity(self, vertex_number, partition_number):
        quotient = vertex_number // partition_number
        remainder = vertex_number % partition_number
        if remainder == 0:
            return quotient
        cnt = 0
        for i in range(partition_number):
            if len(self.partition[i]) == quotient + 1:
                cnt += 1
        if remainder > cnt:
            return quotient + 1
        else:
            return quotient

    def get_neighbors_in_partition(self, vertex_id, partition_id):
        neighbors = 0
        for v in self.partition[partition_id]:
            if self.connections[vertex_id][v] != 0 and self.connections[v][vertex_id] != 0:
                neighbors += 1                
        return neighbors

    def ldg_partition(self, vertex_id):
        w_max = -1;
        res = -1;
        capacity = self.get_capacity(self.parachain_number, self.relaychain_number)
        q = []
        for i in range(self.relaychain_number):
            w = (1 - (len(self.partition[i]) / capacity)) * self.get_neighbors_in_partition(vertex_id, i)
            if w > w_max:
                if len(self.partition[i]) < capacity:
                    w_max = w
                    res = i
                    q = []
                    q.append(res)
            elif w == w_max:
                q.append(i)
        r = random.randint(0, len(q)-1)
        res = q[r]
        return res

    def streaming_partition(self, stream):
        for i in range(self.relaychain_number):
            self.partition[i].append(stream[i])
        for i in range(self.relaychain_number, self.parachain_number):
            self.partition[self.ldg_partition(stream[i])].append(stream[i])

        for i in range(self.relaychain_number):
            for j in range(len(self.partition[i])):
                self.partition[i][j] += 1000
        self.partition.sort(key = lambda x : len(x))

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

    def main(self):
        stream = [i for i in range(self.parachain_number)]
        random.shuffle(stream)
        self.streaming_partition(stream)
        self.correct()
        relays = self.fitness()
        return relays

if __name__ == '__main__':

    shuffle_num = 1000
    best_fitness = 10000
    for i in range(shuffle_num):
        print("Trial: {}".format(i))
        ldg = LDG()
        fitness = ldg.main()
        if fitness < best_fitness:
            best = ldg.partition
            best_fitness = fitness
            print(best)
            print(best_fitness)

    with open("sharding.json", "r") as json_file:
        f = json.load(json_file)
    f["ldg"][str(config["relaychain_number"]) + "relays"] = best
    with open("sharding.json", "w") as json_file:
        json_file.write(json.dumps(f, indent=4))