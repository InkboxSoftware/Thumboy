gamePath = 'gamesFolder/gameRom.gb'

import serial
import time
from PIL import Image, ImageEnhance
import sys
import os
import cv2 as cv
import math
from threading import Thread

from pyboy import PyBoy
from pyboy import WindowEvent

#variables
longWaitTimeInSeconds = 0.0025;
waitTimeInSeconds = 0.0025;
inputR=1

global buttonPress 
buttonPress = [False, False, False, False, False, False, False, False] #8 buttons on the gameboy

#functions
def scaleNN(filename):
    im = Image.open(filename)
    im3 = ImageEnhance.Contrast(im)
    im3 = im3.enhance(5.0)
    im3.resize((72,40), Image.NEAREST).save("ns" + filename)
    img2 = cv.imread('ns' + filename,0)
    ret,thresh1 = cv.threshold(img2,127,255,cv.THRESH_BINARY)
    cv.imwrite("th" + filename, thresh1)

def getSpriteData(filename):
    #data to return:
    data = [0] * (72 * 5)
            
    img = Image.open(filename)
    img = img.convert('RGB')
    pixels = img.load()
    width = 72
    height = 40
    
    i = 0
    byteheight = 8
    byteIndex = 0
    
    for y in range(height):
        for x in range(width):
            p = pixels[x,y]
            if p[0] >= 216 and p[1] >= 216 and p[2] >= 216:
                #is white, so add 1 to the bit value
                j = (i % width) + (math.floor(i / (byteheight * width)) * width)
                data[j] += math.floor(math.pow(2, byteIndex))
                #print("f " + str(x) + ", " + str(y) + " = " + str(j))
            i += 1
            if (i % width == 0):
                byteIndex = (byteIndex + 1) % 8
    
    return data

def stringToBool(sentHere):
    if "True" in sentHere:
        return True
    return False

def THUMBYIO(screenUpdate):
    # get keyboard input
    ser.write(str.encode("thumby.display.fill(0)\r\x04"))
    ser.write(str.encode("thumby.display.blit(bytearray(" + str(screenUpdate) + "), 0, 0, 72, 40, 0, 0, 0)\r\x04"))  #new screen
    ser.write(str.encode("thumby.display.update()\r\x04"))
    #getting inputs on keys
    ser.write(str.encode("print(str(thumby.buttonA.pressed()) + \"\\n\" + str(thumby.buttonB.pressed()) + \"\\n\" + str(thumby.buttonU.pressed()) + \"\\n\" + str(thumby.buttonD.pressed()) + \"\\n\" + str(thumby.buttonL.pressed()) + \"\\n\" + str(thumby.buttonR.pressed()) + \"\\n\")\r\x04"))  #A
    time.sleep(waitTimeInSeconds)
    out = "Buttons: "
    while ser.inWaiting() > 0:
        out += bytes.decode(ser.read(1))
    #running button presses
    global buttonPress
    buttonPressString = out.split("\r")
    if (len(buttonPressString) < 6):
        return

    
    #keys
    if stringToBool(buttonPressString[0]) and stringToBool(buttonPressString[1]) and not buttonPress[6]: #start
        pyboy.send_input(WindowEvent.PRESS_BUTTON_START)
    elif (not stringToBool(buttonPressString[0]) or not stringToBool(buttonPressString[1])) and not buttonPress[6]:
        pyboy.send_input(WindowEvent.RELEASE_BUTTON_START)
    if not buttonPress[6]:    #A and B if not pressed together
        if stringToBool(buttonPressString[0]) != buttonPress[0]:    #A
            buttonPress[0] = stringToBool(buttonPressString[0])
            if buttonPress[0]:
                pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
            else:
                pyboy.send_input(WindowEvent.RELEASE_BUTTON_A)
        if stringToBool(buttonPressString[1]) != buttonPress[1]:
            buttonPress[1] = stringToBool(buttonPressString[1])
            if buttonPress[1]:
                pyboy.send_input(WindowEvent.PRESS_BUTTON_B)
            else:
                pyboy.send_input(WindowEvent.RELEASE_BUTTON_B)

    if stringToBool(buttonPressString[2]) and stringToBool(buttonPressString[3]) and not buttonPress[7]: #select
        pyboy.send_input(WindowEvent.PRESS_BUTTON_SELECT)
    elif (not stringToBool(buttonPressString[2]) or not stringToBool(buttonPressString[3])) and not buttonPress[7]:
        pyboy.send_input(WindowEvent.RELEASE_BUTTON_SELECT)
    if not buttonPress[7]:    #up and down if not pressed together
        if stringToBool(buttonPressString[2]) != buttonPress[2]:
            buttonPress[2] = stringToBool(buttonPressString[2])
            if buttonPress[2]:
                pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
            else:
                pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)
        if stringToBool(buttonPressString[3]) != buttonPress[3]:
            buttonPress[3] = stringToBool(buttonPressString[3])
            if buttonPress[3]:
                pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
            else:
                pyboy.send_input(WindowEvent.RELEASE_ARROW_DOWN)
    if stringToBool(buttonPressString[4]) != buttonPress[4]:
        buttonPress[4] = stringToBool(buttonPressString[4])
        if buttonPress[4]:
            pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)
        else:
            pyboy.send_input(WindowEvent.RELEASE_ARROW_LEFT)
    if stringToBool(buttonPressString[5]) != buttonPress[5]:
        buttonPress[5] = stringToBool(buttonPressString[5])
        if buttonPress[5]:
            pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)
        else:
            pyboy.send_input(WindowEvent.RELEASE_ARROW_RIGHT)
    return

#begin serial
ser = serial.Serial()

ser.port = 'COM5'
ser.baudrate = 115200
ser.bytesize = serial.EIGHTBITS
ser.open()

#going to raw:
ser.write(str.encode("\r" + "\x03" + "\x03"));  #ctrl-C twice: interrupt any running program
ser.write(str.encode("\r" + "\x01"));

out1 = "T>> "
time.sleep(1)
while ser.inWaiting() > 0:
    out1 += bytes.decode(ser.read(1))
if out1 != '':
    print(str(out1))

ser.write(str.encode("import thumby\r\x04"))  #A
out1 = "T>> "
time.sleep(1)
while ser.inWaiting() > 0:
    out1 += bytes.decode(ser.read(1))
if out1 != '':
    print(str(out1))

#setting up gameboy emulator
pyboy = PyBoy(gamePath, disable_renderer=True, sound=False)   #SOUND OPTIONAL


def runPyBoy():
    frameCap = True
    frameRate = 5 #send a frame to thumby ~every 6 frames
    fCount = 0
    while not pyboy.tick():
        if frameCap:
            fCount += 1
            if fCount >= frameRate:
                fCount = 0
                pil_image = pyboy.screen_image()
                pil_image.save('screenshot.png')
                scaleNN("screenshot.png")
                spriteData = getSpriteData("thscreenshot.png")
                THUMBYIO(spriteData)
        frameCap = not frameCap
        pass
    return

runPyBoy()
