#!/usr/bin/python2.7

import cgi
import serial
import RPi.GPIO as GPIO
import time
import picamera
from subprocess import call
from gpiozero import LED
import os
import sys
import sched, time

scheduler = sched.scheduler(time.time, time.sleep)
time_interval = 60

# set up LED
def on():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(12, GPIO.OUT)
    
def off():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(12, GPIO.IN)

def pic(sc):
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
        image_path = "/home/pi/Captured_Images/" + filename + ".jpg"
        time.sleep(2)
        camera.capture(image_path)
        time.sleep(3)
        print("Successful. Picture is saved at /home/pi/Captured_Images/")
        # invoke the script to get the readings
        try:
            os.system("python3 read_meter.py " + image_path)
        except Exception as e:
            print("Error: ", e)
    sc.enter(time_interval, 1, pic, (sc,))

## Parameter1
# --- "on" : turn on the LED
# --- "off": turn off the LED
# --- "picture": takes a picture and run read_meter on the image to get the reading every minute by default
## Parameter2
# --- time interval between pictures

if len(sys.argv) < 2:
    print ("Please enter argument \"on\", \"off\", or \"picture\" and time interval (in seconds).")
    exit(0)
if len(sys.argv) > 2:
    time_interval = int(sys.argv[2])

if sys.argv[1] == "on":
    on()
elif sys.argv[1] == "off":
    off()
elif sys.argv[1] == "picture":
    scheduler.enter(time_interval, 1, pic, (scheduler,))
    scheduler.run()
