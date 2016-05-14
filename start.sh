#!/bin/bash

cd /root/pi-anemometer

pgrep -f collect_all.py
if [ $? -gt 0 ]; then
  python collect_all.py &
fi

