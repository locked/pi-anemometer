import RPi.GPIO as GPIO
from collections import deque
import time
import json

#GPIO.setmode(GPIO.BOARD)
#pin = 3

GPIO.setmode(GPIO.BCM)
pin = 2

GPIO.setup(pin, GPIO.IN)

wind_dir_list = {
  0: "N",
  1: "NNE",
  2: "NE",
  3: "ENE",
  4: "E",
  5: "ESE",
  6: "SE",
  7: "SSE",
  8: "S",
  9: "SSW",
  10: "SW",
  11: "WSW",
  12: "W",
  13: "WNW",
  14: "NW",
  15: "NNW"
}

def parse_frame(frame):
  #print frame
  frame_header = frame[0:5]
  #print json.dumps(frame_header)
  if json.dumps(frame_header) <> "[1, 1, 0, 1, 1]":
    #print "invalid frame header"
    return

  print

  wind_dir = frame[5:9]
  wind_dir.reverse()
  wind_speed = frame[9:21]
  wind_speed.reverse()
  wind_dir_minv = [0 if b == 1 else 1 for b in wind_dir]
  wind_speed_minv = [0 if b == 1 else 1 for b in wind_speed]
  checksum = frame[21:25]
  wind_dir_inv = frame[25:29]
  wind_dir_inv.reverse()
  wind_speed_inv = frame[29:41]
  wind_speed_inv.reverse()

  print "dir:   ", wind_dir, wind_dir_minv
  print "inv dir:   ", wind_dir_inv
  if wind_dir_minv != wind_dir_inv:
    print "wind direction mismatch"
    #return

  print "speed: ", wind_speed, wind_speed_minv
  print "inv speed: ", wind_speed_inv
  if wind_speed_minv != wind_speed_inv:
    print "wind speed mismatch"
    #return

  print "checksum: ", checksum

  wind_dir_int = int("".join([str(b) for b in wind_dir_minv]), 2)
  wind_speed_int = int("".join([str(b) for b in wind_speed_minv]), 2)
  print "dir int:   ", wind_dir_int, wind_dir_list[wind_dir_int]
  print "speed int: ", wind_speed_int
  

raw_frame = []
first = 0
while True:
  v = GPIO.input(pin)

  elapsed_since_first = int(round(time.time() * 1000)) - first
  if elapsed_since_first > 49:
    # Data raw_frame is about 50 msec length,
    # if duration > 100, reset
    if len(raw_frame) > 0:
      #print "Data Frame (length:%d):" % len(raw_frame)
      frame = raw_frame[0:41]
      parse_frame(frame)
    raw_frame = []
    first = 0
  if len(raw_frame) == 0 and v == 1:
    first = int(round(time.time() * 1000))
  if first > 0:
    raw_frame.append(v)

  #elapsed = int(round(time.time() * 1000)) - start
  #print elapsed
  #while elapsed < 1:
  #  time.sleep(0.000001)
  #  elapsed = int(round(time.time() * 1000)) - start

  #time.sleep(0.00095)  # not too bad
  #time.sleep(0.00094)  # good too
  time.sleep(0.00093)  # best ?

