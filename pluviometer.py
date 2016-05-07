import RPi.GPIO as GPIO
import time
import json
import sys

#GPIO.setmode(GPIO.BOARD)
#pin = 3

GPIO.setmode(GPIO.BCM)
pin = 17

GPIO.setup(pin, GPIO.IN)

count_one = 0
last_v = 0
while True:
  v = GPIO.input(pin)
  if last_v == 1 and v == 1:
    count_one += 1
  else:
    if count_one >= 8 and v == 0:
      print "Bascule with %d" % count_one
    count_one = 0
  last_v = v
  if count_one > 3:
    print count_one
  #sys.stdout.write(str(v))
  #sys.stdout.flush()
  time.sleep(0.004)
