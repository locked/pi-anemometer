#!/usr/bin/python
import RPi.GPIO as GPIO
#from collections import deque
import time
import json
import sys
import re
import logging
import resource
import requests
import threading
from subprocess import *
from multiprocessing import Queue
import Adafruit_BMP.BMP085 as BMP085
import Adafruit_MCP9808.MCP9808 as MCP9808

GPIO.setmode(GPIO.BCM)


class Anemometer(threading.Thread):
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
    GPIO.setup(self.pin, GPIO.IN)

  def parse_frame(self, frame):
    #print frame
    frame_header = frame[0:5]
    #print json.dumps(frame_header)
    if json.dumps(frame_header) <> "[1, 1, 0, 1, 1]":
      #print "invalid frame header"
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
  
  def run(self):
    self.init_gpio()
    raw_frame = []
    first = 0
    freq_delay = 0.001
    freq_delay2 = freq_delay + 0.0003
    #print time.time()
    while True:
      start = int(round(time.time() * 1000000))
      v = GPIO.input(self.pin)
    
      if len(raw_frame) >= 41:
        # Data raw_frame is 41 bits long and last about 49 msec
        if len(raw_frame) > 0:
          frame = raw_frame[0:41]
          #logging.info("Data Frame (length:%d): [%s]" % (len(raw_frame), json.dumps(frame)))
          #time_since_last_frame = int(round(time.time() * 1000000)) - last_frame
          #print time_since_last_frame # ~ 2140000
          self.parse_frame(frame)
          time.sleep(1.9)
          #last_frame = int(round(time.time() * 1000000))
        raw_frame = []
        first = 0
      freq = None
      if len(raw_frame) == 0 and v == 1:
        first = int(round(time.time() * 1000000))
        freq = freq_delay2
      if first > 0:
        raw_frame.append(v)
        freq = freq_delay
    
      if freq: time.sleep(freq)


class Pluviometer(threading.Thread):
  pin = 17

  def init_gpio(self):
    GPIO.setup(self.pin, GPIO.IN)

  def run(self):
    self.init_gpio()
    count_one = 0
    last_v = 0
    start_time = time.time()
    while True:
      v = GPIO.input(self.pin)
      if last_v == 1 and v == 1:
        count_one += 1
      else:
        if count_one >= 8 and v == 0:
          #print "Bascule with %d" % count_one
          if (time.time() - start_time) > 120:
            # Ignore first 2 minutes signal, as it seems to be bogus
            item = {"type": "pluvio", "sensor": "external", "ts": time.time(), "value": count_one}
            q.put(item)
        count_one = 0
      last_v = v
      #if count_one > 3:
      #  print count_one
      time.sleep(0.004)


class Temp(threading.Thread):
  # Convert celsius to fahrenheit.
  def c_to_f(self, c):
    return c * 9.0 / 5.0 + 32.0

  def init_i2c(self):
    self.sensor_mcp = MCP9808.MCP9808()
    self.sensor_mcp.begin()
    self.sensor_bmp = BMP085.BMP085()


  def readRpiSoC(self):
    cmd = ["/opt/vc/bin/vcgencmd", "measure_temp"]
    out = Popen(cmd, stdout=PIPE)
    (sout, _) = out.communicate()
    gs = re.match("temp=([0-9\.]+)", sout)
    return float(gs.group(1)) if gs else None

  def run(self):
    self.init_i2c()
    while True:
      #temp = self.sensor_mcp.readTempC()
      #print 'Temp(MCP): {0:0.3F} *C'.format(temp)
      #print 'Temp(BMP): {0:0.3f} *C'.format(self.sensor_bmp.read_temperature())
      #print 'Pressure = {0:0.2f} Pa'.format(sensor.read_pressure())
      #print 'Altitude = {0:0.2f} m'.format(sensor.read_altitude())
      #print 'Sealevel Pressure = {0:0.2f} Pa'.format(sensor.read_sealevel_pressure())
      item = {"type": "temp", "sensor": "mcp", "ts": time.time(), "value": self.sensor_mcp.readTempC()}
      q.put(item)
      item = {"type": "temp", "sensor": "bmp", "ts": time.time(), "value": self.sensor_bmp.read_temperature()}
      q.put(item)
      item = {"type": "pressure", "sensor": "bmp", "ts": time.time(), "value": self.sensor_bmp.read_pressure()}
      q.put(item)
      item = {"type": "altitude", "sensor": "bmp", "ts": time.time(), "value": self.sensor_bmp.read_altitude()}
      q.put(item)
      temp_soc = self.readRpiSoC()
      if temp_soc:
        item = {"type": "temp", "sensor": "rpi", "ts": time.time(), "value": temp_soc}
        q.put(item)
      #item = {"type": "sealevel_pressure", "sensor": "bmp", "ts": time.time(), "value": self.sensor_bmp.read_sealevel_pressure()}
      #q.put(item)
      time.sleep(120)

def get_memory_usage():
  return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000


logging.basicConfig(filename='/var/log/weather.log', format='%(asctime)s %(message)s', level=logging.INFO)
logging.info("start")

q = Queue()

a = Anemometer()
a.daemon = True
a.start()
#a = Pluviometer()
#a.daemon = True
#a.start()
a = Temp()
a.daemon = True
a.start()

ws_url = "http://php.lunasys.fr/weather/save.php"

max_items = 5000
items = []
while True:
  while not q.empty():
    item = q.get()
    items.append(item)

  #print "items before:", len(items)

  if len(items) > 0:
    #print items
    #data = "items="+json.dumps(items)
    headers = {'content-type': 'application/json'}
    try:
      res = requests.post(ws_url, data=json.dumps({"items": items}), headers=headers, timeout=60)
      if res.status_code == 200 and res.json()['status'] == 0:
        items = []
      else:
        logging.error("error when sending data, invalid return code:[%d] or invalid response" % (int(res.status_code), res.text))
        time.sleep(300)
    except Exception as e:
      logging.error("exception when sending data:[%s]" % str(e))
      time.sleep(300)

  if len(items) > max_items:
    logging.warning("max items [%d/%d] reached" % (len(items), max_items))
    try:
      memory_usage = get_memory_usage()
      logging.warning("max items memory_usage:[%dMB]" % int(memory_usage))
    except:
      pass
    items = items[-max_items:]

  #print "items:", len(items)

  time.sleep(60)

logging.info("end")
