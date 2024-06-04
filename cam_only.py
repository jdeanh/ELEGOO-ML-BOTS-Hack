#%% Load modules
from IPython import get_ipython
import numpy as np
import socket
import sys
import json
import re
import matplotlib.pyplot as plt


import cv2
import requests

import pygame
import os

import logging
import threading

from tkinter import *
from tkinter.ttk import *
from urllib.request import urlopen
import time

'''
INFO SECTION
- if you want to monitor raw parameters of ESP32CAM, open the browser and go to http://192.168.x.x/status
- command can be sent through an HTTP get composed in the following way http://192.168.x.x/control?var=VARIABLE_NAME&val=VALUE (check varname and value in status)
'''
#%% Clear working space
get_ipython().magic('clear')
get_ipython().magic('reset -f')
plt.close('all')

cmd_no = 0
#%% Stream thread function
def stream_function():

    # ESP32 URL
    URL = "http://192.168.4.1"
    AWB = True
    cap = cv2.VideoCapture(URL + ":81/stream")
    
    while True:

        if cap.isOpened():
            
            ret, frame = cap.read()

            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)

            cv2.imshow("frame", frame)

            key = cv2.waitKey(1)
            
            if key == ord('r'):
                idx = int(input("Select resolution index: "))
                set_resolution(URL, index=idx, verbose=True)

            elif key == ord('q'):
                val = int(input("Set quality (10 - 63): "))
                set_quality(URL, value=val)

            elif key == ord('a'):
                AWB = set_awb(URL, AWB)

            elif key == 27:
                break
            
    cv2.destroyAllWindows()
    cap.release()
    car.close()
    
    
#%% Controller thread function
def controller_function(name):
    pygame.init()
    running = True
    LEFT, RIGHT, UP, DOWN = False, False, False, False
    speed = 120
    clock = pygame.time.Clock()
    #Initialize controller
    joysticks = []
    
    for i in range(pygame.joystick.get_count()):
        joysticks.append(pygame.joystick.Joystick(i))
    for joystick in joysticks:
        joystick.init()

    with open(os.path.join("ps4_keys.json"), 'r+') as file:
        button_keys = json.load(file)
    # 0: Left analog horizonal, 1: Left Analog Vertical, 2: Right Analog Horizontal
    # 3: Right Analog Vertical 4: Left Trigger, 5: Right Trigger
    analog_keys = {0:0, 1:0, 2:0, 3:0, 4:-1, 5: -1 }

    analog_zero = True
    prev_dir = ""
    # START OF GAME LOOP
    while running:
        
        ################################# CHECK PLAYER INPUT #################################
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                ############### UPDATE SPRITE IF SPACE IS PRESSED #################################
                pass

            # HANDLES BUTTON PRESSES
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == button_keys['left_arrow']:
                    cmd(car, do = 'move_timed', where = 'left', at = speed)
                if event.button == button_keys['right_arrow']:
                    cmd(car, do = 'move_timed', where = 'right', at = speed)
                if event.button == button_keys['down_arrow']:
                    cmd(car, do = 'move_timed', where = 'back', at = speed)
                if event.button == button_keys['up_arrow']:
                    cmd(car, do = 'move_timed', where = 'forward', at = speed)
                if event.button == button_keys['square']:
                    running = False
                if event.button == button_keys['L1']:
                    cmd(car, do = 'rotate', at = 180)
                if event.button == button_keys['R1']:
                    cmd(car, do = 'rotate', at = 0)
 
            # HANDLES BUTTON RELEASES
            if event.type == pygame.JOYBUTTONUP:
                if event.button == button_keys['left_arrow']:
                    LEFT = False
                if event.button == button_keys['right_arrow']:
                    RIGHT = False
                if event.button == button_keys['down_arrow']:
                    DOWN = False
                if event.button == button_keys['up_arrow']:
                    UP = False
                if event.button == button_keys['L1']:
                    cmd(car, do = 'rotate', at = 90)
                if event.button == button_keys['R1']:
                    cmd(car, do = 'rotate', at = 90)
                
                
            #HANDLES ANALOG INPUTS
            if event.type == pygame.JOYAXISMOTION:
                analog_keys[event.axis] = event.value
                #print(analog_keys)
                
                direction = ""
                
                # Horizontal Analog
                if abs(analog_keys[0]) > .4:
                    if analog_keys[0] < -.7:
                        LEFT = True
                        direction += "left"
                    else:
                        LEFT = False
                    if analog_keys[0] > .7:
                        RIGHT = True
                        direction += "right"
                    else:
                        RIGHT = False
                # Vertical Analog
                if abs(analog_keys[1]) > .4:
                    if analog_keys[1] < -.7:
                        UP = True
                        direction += "forward"
                    else:
                        UP = False
                    if analog_keys[1] > .7:
                        #cmd(car, do = 'move', where = 'back', at = speed)
                        DOWN = True
                        direction += "back"
                    else:
                        DOWN = False                        
                
                if direction == "" and analog_zero == False:
                    analog_zero = True;
                    cmd(car, do = "move_analog", where="", )
                if not direction == "" and not prev_dir == direction:
                    print(direction)
                    analog_zero = False;
                    prev_dir = direction
                    cmd(car, do = 'move_analog', where = direction, at = speed)
                        
        clock.tick(60)
#%% ESP32 Cam Settings CMDs
def set_resolution(url: str, index: int=1, verbose: bool=False):
    try:
        if verbose:
            resolutions = "10: UXGA(1600x1200)\n9: SXGA(1280x1024)\n8: XGA(1024x768)\n7: SVGA(800x600)\n6: VGA(640x480)\n5: CIF(400x296)\n4: QVGA(320x240)\n3: HQVGA(240x176)\n0: QQVGA(160x120)"
            print("available resolutions\n{}".format(resolutions))

        if index in [10, 9, 8, 7, 6, 5, 4, 3, 0]:
            requests.get(url + "/control?var=framesize&val={}".format(index))
        else:
            print("Wrong index")
    except:
        print("SET_RESOLUTION: something went wrong")

def set_quality(url: str, value: int=1, verbose: bool=False):
    try:
        if value >= 10 and value <=63:
            requests.get(url + "/control?var=quality&val={}".format(value))
    except:
        print("SET_QUALITY: something went wrong")

def set_awb(url: str, awb: int=1):
    try:
        awb = not awb
        requests.get(url + "/control?var=awb&val={}".format(1 if awb else 0))
    except:
        print("SET_QUALITY: something went wrong")
    return awb


#%% Send a command and receive a response
off = [0.007,  0.022,  0.091,  0.012, -0.011, -0.05]
def cmd(sock, do, what = '', where = '', at = ''):
    global cmd_no
    cmd_no += 1
    msg = {"H":str(cmd_no)} # dictionary
    if do == 'move':
        msg["N"] = 3
        what = ' car '
        if where == 'forward':
            msg["D1"] = 3
        elif where == 'back':
            msg["D1"] = 4
            msg["T"] = 500
        elif where == 'left':
            msg["D1"] = 1
        elif where == 'right':
            msg["D1"] = 2
        msg["D2"] = at # at is speed here
        where = where + ' '
    elif do == 'move_timed':
        msg["N"] = 2
        what = ' car '
        if where == 'forward':
            msg["D1"] = 3
            msg["T"] = 500
        elif where == 'back':
            msg["D1"] = 4
            msg["T"] = 500
        elif where == 'left':
            msg["D1"] = 1
            msg["T"] = 260
        elif where == 'right':
            msg["D1"] = 2
            msg["T"] = 260
        msg["D2"] = at # at is speed here
        where = where + ' '
    elif do == 'move_analog':
        msg["N"] = 102
        what = ' car '
        if where == 'forward':
            msg["D1"] = 1
        elif where == 'back':
            msg["D1"] = 2
        elif where == 'left':
            msg["D1"] = 3
        elif where == 'right':
            msg["D1"] = 4
        elif where == 'leftforward':
            msg["D1"] = 5
        elif where == 'rightback':
            msg["D1"] = 6
        elif where == 'rightforward':
            msg["D1"] = 7
        elif where == 'rightback':
            msg["D1"] = 8
        else:
            msg["D1"] = 9
        msg["D2"] = at # at is speed here
        where = where + ' '
    elif do == 'stop':
        msg.update({"N":1,"D1":0,"D2":0,"D3":1})
        what = ' car'
    elif do == 'rotate':
        msg.update({"N":5,"D1":1,"D2":at}) # at is an angle here
        what = ' ultrasonic unit'
        where = ' '    
    elif do == 'measure':
        if what == 'distance':
            msg.update({"N":21,"D1":2})
        elif what == 'motion':
            msg["N"] = 6
        what = ' ' + what
    elif do == 'check':
        msg["N"] = 23
        what = ' off the ground'
    msg_json = json.dumps(msg)
    print(str(cmd_no) + ': ' + do + what + where + str(at), end = ': ')
    try:
        sock.send(msg_json.encode())
    except:
        print('Error: ', sys.exc_info()[0])
        sys.exit()
    while 1:
        res = sock.recv(1024).decode()
        print(res)
        res = res.replace("{Heartbeat}", "")
        if '_' in res:
            break
    res = re.search('_(.*)}', res).group(1)
    if res == 'ok' or res == 'true':
        res = 1
    elif res == 'false':
        res = 0
    #elif msg.get("N") == 5:
    #    time.sleep(0.5)                     # give time to rotate head
    elif msg.get("N") == 6:
        res = res.split(",")
        res = [int(x)/16384 for x in res] # convert to units of g
        res[2] = res[2] - 1 # subtract 1G from az
        res = [round(res[i] - off[i], 4) for i in range(6)]
    elif msg.get("N") == 21:
        res = round(int(res)*1.3, 1)        # UM distance with correction factor
    else:
        res = int(res)
    print(res)
    return res

#%% Plot MPU data


#%% MPU Plot Update
def plt_update(mot):
    global ag
    ag = np.vstack((ag, mot))
    plt.clf()
    for i in range(6):
        plt.plot(ag[:,i], label = ag_name[i])
    plt.legend(loc = 'upper left')
    plt.pause(0.01)
    plt.show()
#%% Connect to car's Wifi
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
# print('Receive from {0}:{1}'.format(ip, port))
# try:
#     data = car.recv(1024).decode()
# except:
#     print('Error: ', sys.exc_info()[0])
#     sys.exit()
# print('Received: ', data)

#%% Buttons


#%% Main
if __name__ == '__main__':

    while True:
        stream_function("test")
