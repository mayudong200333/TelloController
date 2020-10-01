from PathMaker import Pathmaker
import matplotlib.pyplot as plt


path = Pathmaker(100)

x,y = path.circle_path(10)

plt.scatter(x,y)
plt.show()