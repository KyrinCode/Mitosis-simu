import random
import copy

from config import config_data

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
    generate_config_generator()
