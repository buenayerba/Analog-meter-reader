import RPi.GPIO as GPIO
import time
import picamera

# set up LED
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(12, GPIO.OUT)

GPIO.output(12, GPIO.LOW)
time.sleep(1)

t = int(time.time())

with picamera.PiCamera() as camera:
    camera.resolution = (1920, 1440)
    camera.vflip = True
    camera.hflip = True

    print("LED ON")
    GPIO.output(12, GPIO.HIGH)
    time.sleep(3)
    camera.flash_mode = 'on'
    camera.capture("captured_images/img_{}.jpg".format(t))
    time.sleep(3)
    print("LED OFF")
    GPIO.output(12, GPIO.LOW)
    
