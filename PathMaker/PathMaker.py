# make path in 2D (x,y)
import numpy as np
import matplotlib.pyplot as plt

class PathMaker:
    def __init__(self,n,dt=0.05):
        self.n = n
        self.dt = dt
        self.t = np.arange(0,(n-1)*dt,dt)

    def circle_path(self,r):
        theta = np.linspace(0,2*np.pi,self.n)
        x = r*np.cos(theta)
        y = r*np.sin(theta)
        return x,y

    def calc_path_v(self,x,y):
        vx = np.diff(x,n=1)/self.dt
        vy = np.diff(y,n=1)/self.dt
        #vx=np.append(0,vx)
        #vy=np.append(0,vy)
        return vx,vy

    def clac_path_a(self,vx,vy):
        ax = np.diff(vx,n=1)/self.dt
        ay = np.diff(vy,n=1)/self.dt
        #ax = np.append(0,ax)
        #ay = np.append(0,ay)
        return ax,ay

if __name__ == "__main__":
    #test
    n = 200
    path = PathMaker(n)
    x, y = path.circle_path(1)

    vx, vy = path.calc_path_v(x, y)
    ax, ay = path.clac_path_a(vx,vy)
    plt.plot(range(len(vx)),vx)
    plt.show()
    plt.plot(range(len(ay)),ay)
    plt.show()

