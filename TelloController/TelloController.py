import logging
import contextlib
import socket
import sys
import threading
from time import sleep
import re

logging.basicConfig(level=logging.INFO,stream=sys.stdout)
logger = logging.getLogger(__name__)

DEFAULT_DISTANCE = 0.30
DEFAULT_SPEED = 10
DEFAULT_DEGREE = 10
INTERVAL = 0.05

class TelloController(object):
    def __init__(self,host_ip='192.168.10.2',host_port=8889,
                 drone_ip='192.168.10.1',drone_port=8889,
                 is_imperial=False, speed = DEFAULT_SPEED , receive_state=True):
        self.host_ip = host_ip
        self.host_port = host_port
        self.drone_ip = drone_ip
        self.drone_address = (drone_ip,drone_port)
        self.is_imperial = is_imperial
        self.speed = speed
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.bind((self.host_ip,self.host_port))

        self.socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket2.bind((self.host_ip, 8890))

        self.response = None
        self.stop_event = threading.Event()
        self._response_thread = threading.Thread(target=self.receive_response,
                                           args=(self.stop_event,))
        self._response_thread.start()

        self.patrol_event = None
        self.is_patrol = False
        self._patrol_semaphore = threading.Semaphore(1)
        self._thread_patrol = None

        self.send_command('command')
        self.send_command('streamon')

        self.pitch_now = None
        self.roll_now = None
        self.yaw_now = None

        self.vgx_now = None
        self.vgy_now = None
        self.vgz_now = None

        self.agx_now = None
        self.agy_now = None
        self.agz_now = None

        self.pitch = []
        self.roll = []
        self.yaw = []

        self.vx = []
        self.vy = []

        # for log the path
        self.islog_path = True
        self.px = [0,]
        self.py = [0,]


        if receive_state:  # for receive the drone state
            self.socket2.sendto('command'.encode('utf-8'), self.drone_address)
            self._state_thread = threading.Thread(target=self.receive_state,args=(self.stop_event,))
            self._state_thread.start()

    def receive_response(self,stop_event):
        while not stop_event.is_set():
            try:
                self.response,ip = self.socket.recvfrom(3000)
                logger.info({'action':'receive_response',
                             'response':self.response})
            except socket.error as ex:
                logger.error({'action':'receive_response',
                              'ex':ex})
                break

    def receive_state(self,stop_event):
        while not stop_event.is_set():
            try:
                response, ip = self.socket2.recvfrom(1024)
                if response == 'ok':
                    continue
                response = response.decode()
                #print(response)
                out = response.replace(';', ' ')
                out = re.findall(r'[+-]?\d+', out)
                #log the pitch,roll yaw
                self.pitch.append(float(out[0]))
                self.roll.append(float(out[1]))
                self.yaw.append(float(out[2]))
                #log the vx and vy
                self.vx.append(float(out[3]))
                self.vy.append(float(out[4]))
                #get the pitch roll yaw and vx,vy,vz,ax,ay,az now
                self.pitch_now = float(out[0])
                self.roll_now = float(out[1])
                self.yaw_now = float(out[2])
                self.vgx_now = float(out[3])
                self.vgy_now = float(out[4])
                self.vgz_now = float(out[5])
                self.agx_now = float(out[13])
                self.agy_now = float(out[14])
                self.agz_now = float(out[15])
                #log the path
                if self.islog_path:
                    x_new = self.px[-1] + INTERVAL * float(self.vgx_now) + INTERVAL ** 2 / 2 * float(self.agx_now)
                    y_new = self.py[-1] + INTERVAL * float(self.vgy_now) + INTERVAL ** 2 / 2 * float(self.agy_now)
                    self.px.append(x_new)
                    self.py.append(y_new)
                sleep(INTERVAL)
            except socket.error as ex:
                logger.error({'action': 'receive_response',
                              'ex': ex})
                break


    def __dell__(self):
        self.stop()

    def stop(self):
        self.stop_event.set()
        retry = 0
        while self._response_thread.isAlive() or self._state_thread.isAlive():
            sleep(0.3)
            if retry > 30:
                break
            retry += 1
        self.socket.close()

    def send_command(self,command):
        logger.info({'action':'send_command','command':command})
        self.socket.sendto(command.encode('utf-8'),self.drone_address)

        retry = 0
        while self.response is None:
            #sleep(0.3)
            if retry == 0:
                break
            retry += 1

        if self.response is None:
            response = None
        else:
            response = self.response.decode('utf-8')
        self.response = None
        return response

    def takeoff(self):
        return self.send_command('takeoff')

    def land(self):
        return self.send_command('land')

    def move(self, direction, distance):
        distance = float(distance)
        if self.is_imperial:
            distance = int(round(distance*30.48))
        else:
            distance = int(round(distance * 100))

        return self.send_command(f'{direction} {distance}')

    def up(self, distance = DEFAULT_DISTANCE):
        return self.move('up',distance)

    def down(self, distance = DEFAULT_DISTANCE):
        return self.move('down',distance)

    def left(self, distance = DEFAULT_DISTANCE):
        return self.move('left',distance)

    def right(self, distance = DEFAULT_DISTANCE):
        return self.move('right',distance)

    def forward(self, distance = DEFAULT_DISTANCE):
        return self.move('forward',distance)

    def back(self, distance = DEFAULT_DISTANCE):
        return self.move('back',distance)

    def set_speed(self,speed):
        return self.send_command(f'speed {speed}')

    def clockwise(self,degree=DEFAULT_DEGREE):
        return self.send_command(f'cw {degree}')

    def counter_clockwise(self,degree=DEFAULT_DEGREE):
        return self.send_command(f'ccw {degree}')

    def flip_front(self):
        return self.send_command(f'flip f')

    def flip_back(self):
        return self.send_command(f'flip b')

    def flip_left(self):
        return self.send_command(f'flip l')

    def flip_right(self):
        return self.send_command(f'flip r')

    def set_rc(self,a,b,c,d):
        return self.send_command(f'rc {a} {b} {c} {d}')

    def patrol(self):
        if not self.is_patrol:
            self.patrol_event = threading.Event()
            self._thread_patrol = threading.Thread(
                target=self._patrol,
                args=(self._patrol_semaphore,self.patrol_event,))
            self._thread_patrol.start()
            self.is_patrol = True

    def stop_patrol(self):
        if self.is_patrol:
            self.patrol_event.set()
            retry = 0
            while self._thread_patrol.isAlive():
                sleep(0.3)
                if retry > 300:
                    break
                retry += 1
            self.is_patrol = False

    def _patrol(self,semaphore,stop_event):
        is_acquire = semaphore.acquire(blocking=False)
        if is_acquire:
            logger.info({'action':'_patrol','status':'acquire'})
            with contextlib.ExitStack() as stack:
                stack.callback(semaphore.release)
                status = 0
                while not stop_event.is_set():
                    status += 1
                    if status == 1:
                        self.up()
                    if status == 2:
                        self.clockwise(90)
                    if status == 3:
                        self.down()
                    if status == 4:
                        status = 0
                    sleep(5)
        else:
            logger.warning({'action':'_patrol','status':'not_acquire'})




if __name__ == '__main__':
    drone_manage = TelloController()

    drone_manage.takeoff()
    sleep(5)
    drone_manage.set_rc(20,20,0,0)
    sleep(0.2)
    drone_manage.set_rc(-20,-20,0,0)
    sleep(0.2)
    drone_manage.land()
    drone_manage.stop()






