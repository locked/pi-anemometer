#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import json
import sys
import re
import logging
import resource
import requests
import threading
from subprocess import *



class Anemometer():
  pin = 18
  last_wind_dir_int = None

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

  def init_gpio(self):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(self.pin, GPIO.IN)

  def parse_frame(self, frame):
    print frame
    frame_header = frame[0:5]
    #print json.dumps(frame_header)
    if json.dumps(frame_header) <> "[1, 1, 0, 1, 1]":
      print "invalid frame header", frame_header
      return

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
  
    #print "dir:   ", wind_dir, wind_dir_minv
    #print "inv dir:   ", wind_dir_inv
    if wind_dir_minv != wind_dir_inv:
      #logging.error("wind direction mismatch")
      return
  
    #print "speed: ", wind_speed, wind_speed_minv
    #print "inv speed: ", wind_speed_inv
    if wind_speed_minv != wind_speed_inv:
      #logging.error("wind speed mismatch")
      return
  
    # TODO: verify checksum
    #print "checksum: ", checksum
  
    wind_dir_int = int("".join([str(b) for b in wind_dir_minv]), 2)
    wind_speed_int = int("".join([str(b) for b in wind_speed_minv]), 2)
    #print "dir int:   %d => %s" % (wind_dir_int, self.wind_dir_list[wind_dir_int])
    #print "speed int: %d => %.1f meter/sec" % (wind_speed_int, wind_speed_int * 0.1)

    if self.last_wind_dir_int is not None and self.last_wind_dir_int <> wind_dir_int:
      item = {"type": "wind_direction", "sensor": "external", "ts": time.time(), "value": self.wind_dir_list[wind_dir_int]}
      q.put(item)
    self.last_wind_dir_int = wind_dir_int

    if wind_speed_int > 0:
      item = {"type": "wind_speed", "sensor": "external", "ts": time.time(), "value": round(wind_speed_int * 0.1, 2), "unit": "m/s"}
      q.put(item)
  
  def loop(self):
    self.init_gpio()
    raw_frame = []
    first = 0
    freq_delay = 0.00093
    #freq_delay = 0.00100
    #print time.time()
    last_frame = 0
    while True:
      start = int(round(time.time() * 1000000))
      v = GPIO.input(self.pin)
    
      if len(raw_frame) >= 41:
        # Data raw_frame is 41 bits long and last about 49 msec
        if len(raw_frame) > 0:
          frame = raw_frame[0:41]
          #logging.info("Data Frame (length:%d): [%s]" % (len(raw_frame), json.dumps(frame)))
          time_since_last_frame = int(round(time.time() * 1000000)) - last_frame
          #print time_since_last_frame # ~ 2140000
          self.parse_frame(frame)
          time.sleep(1.9)
          last_frame = int(round(time.time() * 1000000))
        raw_frame = []
        first = 0
      freq = None
      if len(raw_frame) == 0 and v == 1:
        first = int(round(time.time() * 1000000))
        freq = freq_delay + freq_delay/3
      if first > 0:
        raw_frame.append(v)
        freq = freq_delay
    
      #time.sleep(0.00095)  # not too bad
      #time.sleep(0.00094)  # good too
      #time.sleep(0.00093)  # best ?
      if freq: time.sleep(freq)

