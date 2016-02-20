
== Connection to the Raspberry ==

<pre>
   TX-20    Meaning   RPI
   Brown     TxD      Pin 3 (GPIO 2)
     Red     Vcc      Pin 4 (+5V)
   Green     DTR      Pin 6 (GND)
  Yellow     GND      Pin 6 (GND)
</pre>

When DTR is pulled low (to GND), the device starts sending a data frame every 2 seconds. Each frames last about 49msec, with a bit every 1.2msec.
