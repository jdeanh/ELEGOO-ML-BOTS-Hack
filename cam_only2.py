### Copyright Michael@bots4all
#%% Load modules
from IPython import get_ipython
import numpy as np
import cv2 as cv
from urllib.request import urlopen
import socket
import sys
import json
import re
import matplotlib.pyplot as plt
import time

#%% Clear working space
get_ipython().magic('clear')
get_ipython().magic('reset -f')
plt.close('all')

#%% Capture image from camera
cv.namedWindow('Camera')
cv.moveWindow('Camera', 0, 0)
cmd_no = 0
def capture():
    global cmd_no
    cmd_no += 1
    print(str(cmd_no) + ': capture image')
    cam = urlopen('http://192.168.4.1/capture')
    img = cam.read()
    img = np.asarray(bytearray(img), dtype = 'uint8')
    img = cv.imdecode(img, cv.IMREAD_UNCHANGED)
    cv.imshow('Camera', img)
    # cv.waitKey(1)
    return img


#%% Connect to car's WiFi
ip = "192.168.4.1"
port = 100
print('Connect to {0}:{1}'.format(ip, port))
car = socket.socket()
try:
    car.connect((ip, port))
except:
    print('Error: ', sys.exc_info()[0])
    sys.exit()
print('Connected!')

#%% Read first data from socket
print('Receive from {0}:{1}'.format(ip, port))
try:
    data = car.recv(1024).decode()
except:
    print('Error: ', sys.exc_info()[0])
    sys.exit()
print('Received: ', data)

#%% Main

while 1:
    start_time = time.time()
    # Capture camera image
    capture()
    # Check if car was lifted off the ground to interrupt the while loop
  
#%% Close socket
car.close()