import numpy as np
import matplotlib.pyplot as plt
 
x1 = np.arange(1, 10, 1)
x2 = np.arange(0.1, 1, 0.1)
y1 = np.arange(1, 10, 1)
y2 = np.log(y1)

plt.plot(x1, y1)
# 添加一条坐标轴，y轴的
plt.twiny()
plt.plot(x2, y2)

plt.show()