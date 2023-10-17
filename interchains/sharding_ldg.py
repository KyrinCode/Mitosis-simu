import copy
import numpy as np
import json
import random

from interchains import InterChains
from generator import Generator
from config import config, config_generator

class LDG:
    def __init__(self, recursive_num, simu_num):
        self.recursive_num = recursive_num
        self.simu_num = simu_num
        self.parachain_number = config["parachain_number"]
        self.relaychain_number = config["relaychain_number"]
        self.logic_txs_cnt = 0
        self.generator = Generator(config_generator)
        self.init_adj()
        self.partition = [[] for i in range(self.relaychain_number)]

    def init_adj(self):
        self.adj = [[0 for i in range(self.parachain_number)] for i in range(self.parachain_number)]
        for i in range(self.simu_num):
            logic_txs, num = self.generator.generate_txs(i)
            for logic_tx in logic_txs:
                self.adj[logic_tx.source_chain_id - 1000][logic_tx.dest_chain_id - 1000] += 1
            self.logic_txs_cnt += num

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

    def get_weight_in_partition(self, vertex_id, partition_id):
        weight = 0
        for v in self.partition[partition_id]:
            weight += self.adj[vertex_id][v] + self.adj[v][vertex_id]
        return weight

    def ldg_partition(self, vertex_id):
        w_max = -1;
        res = -1;
        capacity = self.get_capacity(self.parachain_number, self.relaychain_number)
        # int[] numberOfNeighbours = new int[this.numberOfPartitions];
        # loop through all partitionSizes
        q = []
        for i in range(self.relaychain_number):
            # numberOfNeighbours[i] = neighbors_in_partition(i, edgeList);
            #  calculate the formulated value for each partition
            w = (1 - (len(self.partition[i]) / capacity)) * self.get_weight_in_partition(vertex_id, i)
            # print("w: {}, w_max: {}".format(w, w_max))
            if w > w_max:
                if len(self.partition[i]) < capacity:
                    w_max = w
                    res = i
                    q = []
                    q.append(res)
            elif w == w_max:
                q.append(i)
        # print("q: {}".format(q))
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

    def recursive_streaming_partition(self, stream, recursion_num):
        # stream = [21, 85, 47, 53, 9, 75, 68, 72, 94, 61, 16, 76, 48, 44, 15, 27, 56, 38, 62, 7, 57, 52, 80, 64, 28, 2, 54, 82, 71, 12, 93, 63, 26, 39, 42, 3, 55, 69, 19, 86, 36, 20, 46, 81, 77, 24, 74, 60, 8, 6, 58, 66, 97, 70, 5, 59, 32, 1, 11, 31, 18, 0, 91, 84, 78, 37, 51, 67, 13, 90, 23, 83, 34, 43, 41, 98, 17, 25, 49, 45, 4, 22, 79, 88, 73, 40, 50, 30, 99, 14, 95, 29, 89, 33, 65, 92, 87, 96, 35, 10]
        # print("stream: {}".format(stream))
        best_partition = [[]]
        best_fitness = 100

        which_relay = [0 for _ in range(self.parachain_number)]
        for i in range(self.relaychain_number):
            self.partition[i].append(stream[i])
            which_relay[stream[i]] = i
        for i in range(self.relaychain_number, self.parachain_number):
            relay = self.ldg_partition(stream[i])
            self.partition[relay].append(stream[i])
            which_relay[stream[i]] = relay
        for k in range(recursion_num - 1):
            old_partition = copy.deepcopy(self.partition)
            for i in range(self.parachain_number):
                old_relay = which_relay[stream[i]]
                self.partition[old_relay].remove(stream[i])
                relay = self.ldg_partition(stream[i])
                self.partition[relay].append(stream[i])
                if old_relay != relay:
                    which_relay[stream[i]] = relay

            flag = 1
            for k in range(self.relaychain_number):
                if flag == 0:
                    break
                old_l = len(old_partition[k])
                l = len(self.partition[k])
                if old_l != l:
                    flag = 0
                    break
                else:
                    for i in range(l):
                        if old_partition[k][i] != self.partition[k][i]:
                            flag = 0
                            break
            if flag == 1:
                break

            for i in range(self.relaychain_number):
                for j in range(len(self.partition[i])):
                    self.partition[i][j] += 1000

            partition = self.correct_min()
            fitness = self.fitness(partition)
            if fitness < best_fitness:
                best_partition = partition
                best_fitness = fitness
            partition = self.correct_max()
            fitness = self.fitness(partition)
            if fitness < best_fitness:
                best_partition = partition
                best_fitness = fitness

            for i in range(self.relaychain_number):
                for j in range(len(self.partition[i])):
                    self.partition[i][j] -= 1000
        self.partition = best_partition
        return best_fitness
        # self.partition.sort(key = lambda x : len(x))

    def correct_min(self):
        partition = copy.deepcopy(self.partition)
        ruler = []
        for i in range(self.relaychain_number):
            l = self.parachain_number // self.relaychain_number + (1 if self.relaychain_number - i <= self.parachain_number % self.relaychain_number else 0)
            ruler.append(l)

        while 1:
            # 升序排序各中继的平行链数量
            partition.sort(key = lambda x : len(x))
            if len(partition[0]) == ruler[0]:
                break
            
            chain = partition[self.relaychain_number - 1][0] # 找出最后中继中跨片交易最少的平行链
            volumes = [0 for _ in range(self.parachain_number)]
            for i in partition[self.relaychain_number - 1]:
                for j in range(self.parachain_number):
                    if i - 1000 != j:
                        volumes[i - 1000] += (self.adj[i - 1000][j] + self.adj[j][i - 1000])
                if volumes[i - 1000] < volumes[chain - 1000]:
                    chain = i
            
            dest_relay = 0 # 找出未达到平行链数量要求的中继中与该平行链交互最多的中继
            volumes = [0 for _ in range(self.relaychain_number - 1)]
            for k in range(self.relaychain_number - 1):
                if len(partition[k]) >= ruler[k]:
                    break
                for i in partition[k]:
                    volumes[k] += self.adj[chain - 1000][i - 1000] + self.adj[i - 1000][chain - 1000]
                if volumes[k] > volumes[dest_relay]:
                    dest_relay = k
            
            partition[self.relaychain_number - 1].remove(chain)
            partition[dest_relay].append(chain)
        return partition

    def correct_max(self):
        partition = copy.deepcopy(self.partition)
        ruler = []
        for i in range(self.relaychain_number):
            l = self.parachain_number // self.relaychain_number + (1 if self.relaychain_number - i <= self.parachain_number % self.relaychain_number else 0)
            ruler.append(l)

        while 1:
            # 升序排序各中继的平行链数量
            partition.sort(key = lambda x : len(x))
            # if len(partition[relaychain_number - 1]) == ruler[relaychain_number - 1]:
            if len(partition[0]) == ruler[0]:
                break
            
            chain = 0 # 找出最后中继中跨中继占比最高的平行链
            rate = 0
            volumes = []
            for i in partition[self.relaychain_number - 1]:
                tmp_volumes = [0 for _ in range(self.relaychain_number)]
                for j in range(self.parachain_number):
                    for k in range(self.relaychain_number):
                        if j + 1000 in partition[k]:
                            tmp_volumes[k] += (self.adj[i - 1000][j] + self.adj[j][i - 1000])
                tmp_rate = (sum(tmp_volumes) - tmp_volumes[self.relaychain_number - 1]) / sum(tmp_volumes)
                if tmp_rate > rate:
                    chain = i
                    rate = tmp_rate
                    volumes = copy.deepcopy(tmp_volumes)
            
            dest_relay = 0 # 找出未达到平行链数量要求的中继中与该平行链交互最多的中继
            vol = volumes[0]
            for i in range(1, self.relaychain_number):
                if len(partition[i]) >= ruler[i]:
                    break
                if volumes[i] > vol:
                    dest_relay = i
                    vol = volumes[i]
            
            partition[self.relaychain_number - 1].remove(chain)
            partition[dest_relay].append(chain)
        return partition

    def fitness(self, partition): # 令最高占比最小
        parachain_list = [i for j in partition for i in j]
        # print(parachain_list)
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
        # print(tmp_config)
        interchains = InterChains(tmp_config)
        _, _, _, Max = interchains.simulation(self.simu_num)
        return Max

    def main(self):
        stream = [i for i in range(self.parachain_number)]
        random.shuffle(stream)
        # self.streaming_partition(stream)
        return self.recursive_streaming_partition(stream, self.recursive_num)

    def test(self):
        self.partition = [[1061, 1035, 1030, 1093, 1004, 1009, 1010, 1086, 1082, 1088, 1074, 1048, 1020, 1056, 1080, 1098, 1018], [1012, 1007, 1025, 1046, 1003, 1000, 1019, 1026, 1062, 1036, 1044, 1049, 1023, 1057, 1029, 1081, 1076], [1050, 1040, 1041, 1064, 1063, 1053, 1011, 1069, 1070, 1016, 1058, 1033, 1015, 1032, 1002, 1075, 1028, 1085], [1047, 1037, 1060, 1095, 1094, 1077, 1087, 1083, 1055, 1014, 1001, 1022, 1052, 1008, 1065, 1031], [1005, 1034, 1038, 1042, 1092, 1054, 1089, 1078, 1027, 1006, 1051, 1013, 1068, 1043], [1084, 1072, 1045, 1067, 1099, 1079, 1066, 1091, 1096, 1039, 1024, 1017, 1073, 1021, 1059, 1097, 1071, 1090]]
        partition = self.correct_min()
        print(partition)
        

if __name__ == '__main__':

    shuffle_num = 100
    best_fitness = 100
    for i in range(shuffle_num):
        print("Trial: {}".format(i))
        recursive_num = 2 # 最少2
        simu_num = 10
        ldg = LDG(recursive_num, simu_num)
        fitness = ldg.main()
        if fitness < best_fitness:
            best = ldg.partition
            best_fitness = fitness
            print(best)
            print(best_fitness)
    # print(best)
    # print(best_fitness)

    with open("sharding.json", "r") as json_file:
        f = json.load(json_file)
    f["ldg"][str(config["relaychain_number"]) + "relays"] = best
    with open("sharding.json", "w") as json_file:
        json_file.write(json.dumps(f, indent=4))

# ldg = LDG(2, 10)
# ldg.test()