import numpy as np
import matplotlib.pyplot as plt
np.random.seed(100)
data_1 = np.random.normal(100, 10, 200)
data_2 = np.random.normal(70, 30, 200)
data_3 = np.random.normal(80, 20, 200)
data_4 = []
data_to_plot=[data_1, data_2, data_3, data_4]
# data=np.random.normal(size=(100,4),loc=0,scale=1) #表示有4组数据，每组数据有100个
print(data_1)
labels=['A','B','C','D']
plt.boxplot(data_to_plot, labels=labels)
plt.show()