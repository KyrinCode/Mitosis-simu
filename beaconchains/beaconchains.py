import math
import copy

from config import config, config_generator

class BeaconChains:
    def __init__(self, config) -> None:
        self.init_config(config)
        self.init_topology()
        pass

    def init_config(self, config):
        self.parachain_number = config["parachain_number"]
        self.relaychain_number = config["relaychain_number"]
        self.relaychain_blockheader_number = config["relaychain_blockheader_number"]
        self.topology_config = config["topology"]
        
    def init_topology(self):
        self.topology = {}
        for k, v in self.topology_config["one-many"].items():
            self.topology[k] = v[:]
            for id in v:
                self.topology[id] = k
        for i in self.topology_config["many-many"]:
            for j in self.topology_config["many-many"]:
                if j != i:
                    self.topology[i].append(j)

    def check(self):
        if math.ceil(self.parachain_number / self.relaychain_number) > self.relaychain_blockheader_number:
            return False
        return True
    
    def get_total_relays(self):
        sum = 0
        for r in range(self.relaychain_number):
            for p_r in self.topology[r]:
                if p_r >= 1000:
                    sum_tmp = 1
                    for k in range(self.relaychain_number):
                        if r != k:
                            for p_k in self.topology[k]:
                                if p_k >= 1000:
                                    if config_generator["parachain_connection_weights"][p_r - 1000][p_k - 1000] > 0:
                                        sum_tmp += 1
                                        break
                    # print(p_r, sum_tmp)
                sum += sum_tmp
        return sum

if __name__ == '__main__':

    config_x = copy.deepcopy(config)
    tmp = [
        [
            1027,
            1069,
            1033,
            1093,
            1090,
            1045,
            1058,
            1089,
            1017,
            1015,
            1037,
            1020,
            1036,
            1085,
            1004,
            1086,
            1061,
            1064,
            1018,
            1060,
            1080,
            1043,
            1038,
            1009,
            1022
        ],
        [
            1071,
            1063,
            1000,
            1031,
            1098,
            1091,
            1097,
            1070,
            1075,
            1012,
            1094,
            1021,
            1016,
            1077,
            1008,
            1011,
            1013,
            1087,
            1096,
            1041,
            1092,
            1051,
            1068,
            1054,
            1005
        ],
        [
            1083,
            1052,
            1042,
            1074,
            1050,
            1049,
            1032,
            1026,
            1099,
            1046,
            1002,
            1039,
            1088,
            1055,
            1082,
            1040,
            1034,
            1030,
            1095,
            1019,
            1048,
            1067,
            1024,
            1006,
            1081
        ],
        [
            1003,
            1001,
            1053,
            1073,
            1084,
            1062,
            1029,
            1025,
            1056,
            1066,
            1076,
            1065,
            1079,
            1023,
            1044,
            1078,
            1047,
            1007,
            1028,
            1010,
            1059,
            1035,
            1072,
            1057,
            1014
        ]
    ]
    for i in range(config_x["relaychain_number"]):
        config_x["topology"]["one-many"][i] = tmp[i]
    config_x["topology"]["many-many"] = [i for i in range(config_x["relaychain_number"])]
    beaconchains = BeaconChains(config_x)
    print(beaconchains.topology)
    if beaconchains.check():
        print(beaconchains.get_total_relays())