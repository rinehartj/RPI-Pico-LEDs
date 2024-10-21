from machine import Pin, PWM
from utime import sleep
from random import randint
from constants import COLORS, REMCODE, RGBLST
import _thread
from ir_rx.nec import NEC_8
import gc

sleep(1.5)
hexIn = 0
bright = 10 #0-255
brightArr = [5, 10, 15, 30, 80, 150, 255]
pwm = []
led = Pin(25, Pin.OUT)
mode = False
colArr = [[0,0,0],[0,0,0]]
baton = _thread.allocate_lock()
brightLvl = len(brightArr)-1
speed = 10
remColors = [65,88,89,69,68,84,85,73,72,80,81,77,76,28,29,30,31,24,25,26,27]

for i in range(12):
    pwm.append(PWM(Pin(i)))
    pwm[i].freq(1000)
    pwm[i].duty_u16(0)

def u(strip, color, a):#update certain strip only 65025 is highest.
    if strip == 1:
        pwm[0].duty_u16(color[1]*a)
        pwm[1].duty_u16(color[0]*a)
        pwm[2].duty_u16(color[2]*a)
    if strip == 0:
        pwm[3].duty_u16(color[1]*a)
        pwm[4].duty_u16(color[0]*a)
        pwm[5].duty_u16(color[2]*a)
    if strip == 3:
        pwm[6].duty_u16(color[1]*a)
        pwm[7].duty_u16(color[0]*a)
        pwm[8].duty_u16(color[2]*a)
    if strip == 2:
        pwm[9].duty_u16(color[1]*a)
        pwm[10].duty_u16(color[0]*a)
        pwm[11].duty_u16(color[2]*a)

def callback(data, addr, ctrl):
    global hexIn
    if data > 0:  # NEC protocol sends repeat codes.
        hexIn = data

ir = NEC_8(Pin(12, Pin.IN, Pin.PULL_DOWN), callback)

def findRem(val):
    for i in range(11):
        for j in range(4):
            if val == REMCODE[i][j]:
                return i, j    
            
def fourColorSwap(colorA, colorB, colorC, colorD, speed):
    u(0, colorA, bright)
    u(1, colorB, bright)
    u(2, colorC, bright)
    u(3, colorD, bright)
    sleep(speed/50)
    u(0, colorB, bright)
    u(1, colorC, bright)
    u(2, colorD, bright)
    u(3, colorA, bright)
    sleep(speed/50)
    u(0, colorC, bright)
    u(1, colorD, bright)
    u(2, colorA, bright)
    u(3, colorB, bright)
    sleep(speed/50)
    u(0, colorD, bright)
    u(1, colorA, bright)
    u(2, colorB, bright)
    u(3, colorC, bright)
    sleep(speed/50)

def twoFade(colList):
    baton.acquire()
    while mode is True:
#         print(speed)
        for i in range(0, len(colList), speed):
            for j in range(0, 3, 2):
                u(j, colList[i], bright)
                u(j+1, colList[len(colList)-1-i], bright)
            sleep(0.02)
        if mode is True:
            for i in range(len(colList)-1, 0, -speed):
                for j in range(0, 3, 2):
                    u(j, colList[i], bright)
                    u(j+1, colList[len(colList)-1-i], bright)
                sleep(0.02)
    baton.release()

def genTwoColFade(colorA, colorB):
    rate = 253 #resolution, 255 max (255/255=1 step)
    steps = []
    color = [colorA[0], colorA[1], colorA[2]]
    cArray = []
    for i in range(3):
        step = (colorA[i]-colorB[i])/rate
        if step < 0.001 and step > -0.001: step = 0
        steps.append(step)
    for x in range(rate+1):
        cArray.append([int(color[0]), int(color[1]), int(color[2])])
        for i in range(3):
            color[i] -= steps[i]
            if steps[i] > 0.0 and color[i] < colorB[i]: steps[i] = 0.0
            if steps[i] < 0.0 and color[i] > colorB[i]: steps[i] = 0.0
            if color[i] > 255: color[i] = 255.0
            if color[i] < 0.0: color[i] = 0.0
    cArray.append(colorB)
    #print(len(cArray))
    return(cArray)

def solidColor(r, g, b):
    baton.acquire()
    while mode is True:
        for i in range(4):
            u(i, [r,g,b], bright)
        sleep(0.1)
    baton.release()

def twoSolidColor(c):
    baton.acquire()
    while mode is True:
        for i in range(0, 3, 2):
            u(i, c[0], bright)
            u(i+1, c[1], bright)
        sleep(0.2)
    baton.release()

def fourSolidColor(colList):
    baton.acquire()
    while mode is True:
        for i in range(4):
            u(i, colList[i], bright)
        sleep(0.2)
    baton.release()

def oneFade(colList):
    baton.acquire()
    while mode is True:
        for i in range(0, len(colList), speed):
            for j in range(4):
                u(j, colList[i], bright)
            sleep(0.02)
        if mode is True:
            for i in range(len(colList)-1, 0, -speed):
                for j in range(4):
                    u(j, colList[i], bright)
                sleep(0.02)
    baton.release()

def twoFlash(c):
    baton.acquire()
    while mode is True:
        for i in range(0, 3, 2):
            u(i, c[0], bright)
            u(i+1, c[1], bright)
        sleep(10/(speed*2)) # speed factor
        for i in range(0, 3, 2):
            u(i, c[1], bright)
            u(i+1, c[0], bright)
        sleep(10/(speed*2)) # speed factor
    baton.release()

def sweepFlash(c):
    baton.acquire()
    while mode is True:
        for i in range(4):
            if mode is True:
                for j in range(4):
                    u(j, c[1], bright)
                u(i, c[0], bright)
                sleep(5/(speed*2))
        for i in range(2,0,-1):
            if mode is True:
                for j in range(4):
                    u(j, c[1], bright)
                u(i, c[0], bright)
                sleep(5/(speed*2))
    baton.release()

def sweepFade2(colList):
    baton.acquire()
    while mode is True:
        for x in range(4):
            for i in range(0, len(colList), speed):
                u(x, colList[i], bright)
                sleep(0.02)
            if mode is True:
                for i in range(len(colList)-1, 0, -speed):
                    u(x, colList[i], bright)
                    sleep(0.02)
    baton.release()

def sweepFade(colList):
    baton.acquire()
    for i in range(4):
            u(i, colList[0], bright)
    stripOrder = [[0,1],[1,0],[2,1],[3,2],[2,3],[1,2]]
    while mode is True:
        for strip in stripOrder:
            if mode is True:
                for i in range(0, len(colList), speed*2):
                    u(strip[0], colList[i], bright)
                    u(strip[1], colList[len(colList)-1-i], bright)
                    sleep(0.02)
                u(strip[1], colList[0], bright)
                sleep(1/speed)
    baton.release()

def rgb():
    baton.acquire()
    locations = [0, int(1*len(RGBLST)/8), int(2*len(RGBLST)/8), int(3*len(RGBLST)/8)]
    while mode is True:
        for i in range(4):
            u(i, RGBLST[locations[i]], bright)
            locations[i] += 1
            if locations[i] > len(RGBLST)-1: locations[i] = 0
        sleep(0.02)
    baton.release()

def selectCol(num): #num of colors to select, cannot exceed 4
    global hexIn
    colSelect = []
    for i in range(4):
        u(i, [0,0,0], 0)
    for i in range(num):
        while not hexIn in remColors:
            u(i, [255,255,255], 20)
            sleep(0.1)
            u(i, [255,255,255], 0)
            sleep(0.1)
        button = findRem(hexIn)
        if hexIn != 65: colSelect.append(COLORS[button[0]-1][button[1]])
        else: colSelect.append([0,0,0])
        u(i, colSelect[i], bright)
        hexIn = 0
    return colSelect

gc.enable()
gc.mem_alloc()
while True:
    led.toggle()
    if hexIn:
        button = findRem(hexIn)
#         print("value: " + str(hexIn))
#         print(button)
        
        if button[0] >= 1 and button[0] <= 5:
            mode = False
            baton.acquire()
            mode = True
            _thread.start_new_thread(solidColor, (COLORS[button[0]-1][button[1]]))
            baton.release()
            
        if hexIn == 92:
            if brightLvl < len(brightArr)-1:
                brightLvl += 1
            bright = brightArr[brightLvl]
        if hexIn == 93:
            if brightLvl > 0:
                brightLvl -= 1
            bright = brightArr[brightLvl]
        if hexIn == 23:
            if speed < 20:
                speed += 1
#                 print("Speed: " + str(speed))
        if hexIn == 19:
            if speed > 1:
                speed -= 1
#                 print("Speed: " + str(speed))
                
        if hexIn == 64:
            mode = False
            baton.acquire()
            for i in range(4):
                u(i, [0,0,0], bright)
            hexIn = 0
            while hexIn != 64:
                sleep(1)
            for i in range(4):
                u(i, [20,20,20], bright)
            baton.release()
        if hexIn == 12:
            mode = False
            baton.acquire()
            mode = True
            _thread.start_new_thread(twoSolidColor, (selectCol(2),))
            baton.release()
        if hexIn == 8:
            mode = False
            baton.acquire()
            mode = True
            _thread.start_new_thread(fourSolidColor, (selectCol(4),))
            baton.release()
        if hexIn == 13:
            mode = False
            baton.acquire()
            mode = True
            c = selectCol(2)
            _thread.start_new_thread(oneFade, (genTwoColFade(c[0], c[1]),))
            baton.release()
        if hexIn == 14:
            mode = False
            baton.acquire()
            mode = True
            c = selectCol(2)
            _thread.start_new_thread(twoFade, (genTwoColFade(c[0], c[1]),))
            baton.release()
        if hexIn == 9:
            mode = False
            baton.acquire()
            mode = True
            c = selectCol(2)
            _thread.start_new_thread(twoFlash, (c,))
            baton.release()
        if hexIn == 10:
            mode = False
            baton.acquire()
            mode = True
            c = selectCol(2)
            _thread.start_new_thread(sweepFlash, (c,))
            baton.release()
        if hexIn == 11:
            mode = False
            baton.acquire()
            mode = True
            c = selectCol(2)
            _thread.start_new_thread(sweepFade, (genTwoColFade(c[0], c[1]),))
            baton.release()
        if hexIn == 15:
            mode = False
            baton.acquire()
            mode = True
            _thread.start_new_thread(rgb, ())
            baton.release()
        hexIn = 0
    sleep(0.1)


