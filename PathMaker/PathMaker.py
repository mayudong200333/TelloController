# make path in 2D (x,y)
import numpy as np

class Pathmaker:
    def __init__(self,n):
        self.n = n

    def circle_path(self,r):
        theta = np.linspace(0,2*np.pi,self.n)
        x = r*np.cos(theta)
        y = r*np.sin(theta)
        return x,y


