#!/usr/bin/python2.7

import cgi, cgitb
import serial
import RPi.GPIO as GPIO
import time
import picamera
from subprocess import call
from gpiozero import LED

# Output the headers.
print ("Content-Type: text/html") # html content to follow
print                           # blank line, end of headers

# Output the content.
print ("""
<html>
    <head>
        <title>Analog Meter Reader</title>
    </head>
    <body>
        <h1>Analog Meter Reader</h1>
        <p>Select command. ([ON]: turn on the LED, [OFF]: turn off the LED, [PICTURE]: takes a picture)</p>
        <form method="post" action="take_first_picture.py">
            <input type = 'submit' value = 'ON' name="on"/>
            <input type = 'submit' value = 'OFF' name="off"/>
            <input type = 'submit' value = 'PICTURE' name="picture"/>
        </form>
""")

# set up LED
def on():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(12, GPIO.OUT)
    GPIO.output(12, GPIO.HIGH)
    
def off():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(12, GPIO.IN)
    GPIO.output(12, GPIO.LOW)

form = cgi.FieldStorage()
i = 0
if "on" in form:
    on()
elif "off" in form:
    off()
elif "picture" in form:
    i = i + 1
    with picamera.PiCamera() as camera:
        #print("step 1")
        camera.resolution = (1920, 1440)
        #print("step 2")
        camera.vflip = True
        camera.hflip = True
        #print("step 3")
        time.sleep(2)
        camera.flash_mode = 'on'
        #print("step 4")
        filename =(time.strftime("%y-%b-%d_%H:%M"))
        variable = "/home/pi/Captured_Images/" + filename + ".jpg"
        time.sleep(2)
        camera.capture(variable)
        time.sleep(3)
        print("Picture taken")

print ("""
    </body>
</html>
""")