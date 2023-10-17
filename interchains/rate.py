import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from config import Cosmos_crosschain_rate_list

print(Cosmos_crosschain_rate_list[:])
s = pd.DataFrame(np.array(Cosmos_crosschain_rate_list[:]), columns = ['value'])
print(s.head())

fig = plt.figure(figsize = (10,6))
# ax1 = fig.add_subplot(2,1,1)  # 创建子图1
plt.scatter(s.index, s.values)
# ax1.scatter(s.index, s.values)
plt.grid()
# 绘制数据分布图

# ax2 = fig.add_subplot(2,1,2)  # 创建子图2
# s.hist(bins = 50, alpha = 0.5, ax = ax2)
# s.plot(kind = 'kde', secondary_y = True, ax = ax2)
# plt.grid()
# 绘制直方图
# 呈现较明显的正太性
plt.show()