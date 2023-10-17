import random
import math
import copy
import matplotlib.pyplot as plt
import json

from beaconchains import BeaconChains
from config import config

class GA:

    #初始化种群 生成chromosome_length大小的population_size个个体的种群
    def __init__(self, generation_number, population_size, pm, simu_num):
 
        self.generation_number = generation_number
        self.population_size = population_size
        self.pm = pm
        self.simu_num = simu_num
        self.parachain_number = config["parachain_number"]
        self.parachain_ids = [i + 1000 for i in range(self.parachain_number)]
        self.relaychain_number = config["relaychain_number"]

    def species_origin_ldg(self):
        with open("sharding.json", "r") as json_file:
            f = json.load(json_file)
        x = [i for j in f["ldg"][str(self.relaychain_number) + "relays"] for i in j]
        population = []
        for i in range(self.population_size):
            population.append(x)
        return population

    def species_origin_memory(self):
        with open("sharding.json", "r") as json_file:
            f = json.load(json_file)
        population = f["ga"][str(self.relaychain_number) + "relays population"] # [:len(self.population_size)]
        for _ in range(self.population_size - len(population)):
            tmp = self.parachain_ids[:]
            random.shuffle(tmp)
            population.append(tmp)
        return population

    def species_origin(self):
        population = []
        for _ in range(self.population_size):
            tmp = self.parachain_ids[:]
            random.shuffle(tmp)
            population.append(tmp)
        return population

    def fitness(self, population): # 令最高占比最小
        fitness_value = []

        for parachain_list in population:
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
            fitness_value.append(relays)
        return fitness_value

    # def selection(self, population, fitness_value): # 锦标赛
    #     new_population = []
    #     for _ in range(self.population_size):
    #         i1, i2 = random.sample([i for i in range(len(population))], k=2)
    #         if fitness_value[i1] < fitness_value[i2]:
    #             parachain_list = population[i1]
    #         else:
    #             parachain_list = population[i2]
    #         new_population.append(parachain_list)
    #     return new_population

    def selection(self, population, fitness_value): # 排序前k
        new_population = []
        new_fitness_value = []
        sorted_id = sorted(range(len(fitness_value)), key = lambda x: fitness_value[x])
        for i in range(self.population_size):
            new_population.append(population[sorted_id[i]])
            new_fitness_value.append(fitness_value[sorted_id[i]])

        print(new_fitness_value)

        return new_population, new_fitness_value

    def crossover(self, population):
        shuffled_population = copy.deepcopy(population)
        random.shuffle(shuffled_population)
        new_population = []
        for i in range(0, self.population_size, 2):
            pos = 0
            for j in range(self.relaychain_number):
                l = self.parachain_number // self.relaychain_number + (1 if self.relaychain_number - j <= self.parachain_number % self.relaychain_number else 0)
                relay_l = pos
                relay_r = pos + l - 1
                # 对 population[i] 和 population[i+1] 的 [left, right] 随机一段交叉
                # 交叉
                # print("------------------ crossover ------------------")
                tmp_1 = shuffled_population[i][:]
                tmp_2 = shuffled_population[i+1][:]
                # print("tmp_1: ", tmp_1)
                # print("tmp_2: ", tmp_2)
                # print("\n")
                i1, i2 = random.sample([i for i in range(l)], k=2) # 左闭右闭
                i1, i2 = relay_l + i1, relay_l + i2
                if i1 > i2:
                    i1, i2 = i2, i1
                l2 = i2 - i1 + 1
                tmp_3 = tmp_1[i1:i2+1]
                tmp_4 = tmp_2[i1:i2+1]
                # print("tmp_3: ", tmp_3)
                # print("tmp_4: ", tmp_4)
                # print("\n")
                tmp_1, tmp_2 = tmp_1[:i1] + tmp_4[:] + tmp_1[i2+1:], tmp_2[:i1] + tmp_3[:] + tmp_2[i2+1:]
                # print("tmp_1: ", tmp_1)
                # print("tmp_2: ", tmp_2)
                # print("\n")
                # 对 [i1, i2] 排序，双指针找到重复的元素，将重复元素从原 [i1, i2] 剔除，返回数组
                deja = []
                tmp_5 = sorted(tmp_3)
                tmp_6 = sorted(tmp_4)
                # print("tmp_5: ", tmp_5)
                # print("tmp_6: ", tmp_6)
                # print("\n")
                i5 = 0
                i6 = 0
                while i5 < l2 and i6 < l2:
                    if tmp_5[i5] == tmp_6[i6]:
                        deja.append(tmp_5[i5])
                        i5 += 1
                        i6 += 1
                    elif tmp_5[i5] < tmp_6[i6]:
                        i5 += 1
                    else:
                        i6 += 1
                for d in deja:
                    tmp_3.remove(d)
                    tmp_4.remove(d)
                # print("tmp_3: ", tmp_3)
                # print("tmp_4: ", tmp_4)
                # print("\n")
                # 根据数组将 population[i] 和 population[i+1] 中影响的元素对应替换
                l3 = len(tmp_3)
                for k in range(l3):
                    for i_1 in range(self.parachain_number):
                        if (i_1 < i1 or i_1 > i2) and tmp_1[i_1] == tmp_4[k]:
                            tmp_1[i_1] = tmp_3[k]
                    for i_2 in range(self.parachain_number):
                        if (i_2 < i1 or i_2 > i2) and tmp_2[i_2] == tmp_3[k]:
                            tmp_2[i_2] = tmp_4[k]
                new_population.append(tmp_1)
                new_population.append(tmp_2)
                # print("tmp_1: ", tmp_1)
                # print("tmp_2: ", tmp_2)
                # print("-----------------------------------------------")
                pos = relay_r
        return new_population

    def mutation(self, population):
        # 对parachain_list每个位置以pm概率随机选出，shuffle，再放回去
        new_population = []
        for parachain_list in population:
            new_list = parachain_list[:]
            tmp_1 = []
            for i in range(self.parachain_number):
                if random.random() < self.pm:
                    tmp_1.append(i)
            tmp_2 = tmp_1[:]
            random.shuffle(tmp_2)
            l = len(tmp_1)
            for i in range(l):
                new_list[tmp_1[i]] = parachain_list[tmp_2[i]]
            new_population.append(new_list)
        return new_population

    def best(self, population, fitness_value):
 
        l = len(population)
        best_fitness = fitness_value[0]
        best_individual = population[0]
        best_individual_index = 0
        # print(fitness_value)
 
        for i in range(1, l):
            if(fitness_value[i] < best_fitness):
                best_fitness = fitness_value[i]
                best_individual = population[i]
                best_individual_index = i
 
        return best_fitness, best_individual, best_individual_index

    def plot(self, results):
        X = []
        Y = []
 
        for i in range(self.generation_number):
            X.append(i)
            Y.append(results[i])
 
        plt.plot(X, Y)
        plt.show()
 
    def main(self):
        history = []
        global_best_fitness = 10000
        global_best_individual = []

        population = self.species_origin()
        # population = self.species_origin_memory()
        # print("population after species_origin: ", population)
        fitness_value = self.fitness(population)
        for i in range(self.generation_number):
            print("----- generation {} -----".format(i))
            
            next_population = self.crossover(population)
            # print("population after crossover: ", next_population)
            next_population = self.mutation(next_population)
            # print("population after mutation: ", next_population)
            # print("\npopulation: ", population)
            # print("\npopulation fitness: ", fitness_value)
            # print("\nnext_population: ", next_population)
            new_population = population + next_population
            next_fitness_value = self.fitness(next_population)
            # print("\nnext_population fitness: ", next_fitness_value)
            fitness_value += next_fitness_value
            # print("\nnew_population: ", new_population)
            # print("\nnew_population fitness: ", fitness_value)

            best_fitness, best_individual, best_individual_index = self.best(new_population, fitness_value)
            history.append(best_fitness)
            if best_fitness < global_best_fitness:
                global_best_fitness = best_fitness
                global_best_individual = best_individual#[:]
            # print(len(new_population), len(fitness_value))
            population, fitness_value = self.selection(new_population, fitness_value)
            # print("population after selection: ", population)
            
        print(global_best_fitness)
        print(global_best_individual)
        self.plot(history)

        res = self.convert_list(global_best_individual)
        self.save_result(res, population)
    
    def convert_list(self, parachain_list):
        res = []
        pos = 0
        for i in range(self.relaychain_number):
            l = self.parachain_number // self.relaychain_number + (1 if self.relaychain_number - i <= self.parachain_number % self.relaychain_number else 0)
            tmp = []
            for j in range(l):
                tmp.append(parachain_list[pos])
                pos += 1
            res.append(tmp)
        return res

    def save_result(self, res, population):
        with open("sharding.json", "r") as json_file:
            f = json.load(json_file)
        f["ga"][str(self.relaychain_number) + "relays"] = res
        f["ga"][str(self.relaychain_number) + "relays population"] = population
        with open("sharding.json", "w") as json_file:
            json_file.write(json.dumps(f, indent=4))

if __name__ == '__main__':

    generation_number = 1000
    population_size = 20
    pm = 0.1
    simu_num = 10
    ga = GA(generation_number, population_size, pm, simu_num)
    ga.main()