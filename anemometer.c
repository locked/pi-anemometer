#include <stdio.h>
#include <wiringPi.h>
#include <time.h>
#include <sys/time.h>
#include <sched.h>
#include <string.h>
#include <math.h>

/*
 * Requirements:
 *   apt-get install gcc wiringpi
 *
 * Build command:
 *   gcc -o anemometer anemometer.c -lwiringPi -lm
 *
 * Run:
 *   nice -19 ./anemometer
 *
 * Based on:
 *   https://www.john.geek.nz/2011/07/la-crosse-tx20-anemometer-communication-protocol/
 */

long long current_timestamp() {
    struct timeval te; 
    gettimeofday(&te, NULL);
    long long microseconds = te.tv_sec*1000000LL + te.tv_usec;
    return microseconds;
}

int decode(int frame[], int start, int end, int inverted) {
  int i;
  int v = 0;
  for( i = start; i < end; i++ ) {
    //printf("v:%d", frame[i]);
    v = v | (abs(inverted - frame[i]) * (int)pow(2.0, (double)(i - start)));
  }
  return v;
}

void decode_frame(int frame[]) {
      int header, wind_dir, wind_speed, checksum, wind_dir_inv, wind_speed_inv, i;

      for( i=0; i<=41; i++ ) {
        printf(" %d ", frame[i]);
      }
      printf("\n");
      /*
      */

      header = decode(frame, 0, 5, 1);
      if( header != 4 ) {
        printf("Invalid frame: bad header:[%d]\n", header);
        return;
      }

      wind_dir = decode(frame, 5, 9, 1);
      wind_speed = decode(frame, 9, 21, 1);
      checksum = decode(frame, 21, 25, 1);
      wind_dir_inv = decode(frame, 25, 29, 0);
      wind_speed_inv = decode(frame, 29, 41, 0);

      if( wind_dir != wind_dir_inv ) {
        printf("Invalid frame: wind direction mismatch. wind_dir:[%d] wind_dir_inv:[%d]\n", wind_dir, wind_dir_inv);
        return;
      }
      if( wind_speed != wind_speed_inv ) {
        printf("Invalid frame: wind speed mismatch. wind_speed:[%d] wind_speed_inv:[%d]\n", wind_speed, wind_speed_inv);
        return;
      }
      int sum = 0;
      for( i = 5; i < 21; i+=4 ) {
        int v = decode(frame, i, i+4, 1);
        sum += v;
      }
      sum = sum % 16;
      if( sum != checksum ) {
        printf("Invalid frame: bad checksum. sum:[%d] checksum:[%d]\n", sum, checksum);
        return;
      }
      printf("header:[%d] wind_dir:[%d] wind_dir_inv:[%d] wind_speed:[%d] wind_speed_inv:[%d] checksum:[%d]\n", header, wind_dir, wind_dir_inv, wind_speed, wind_speed_inv, checksum);
      fflush(stdout);
}


int main (void) {
  struct timeval tv;
  double t2;
  int i, v;
  struct timespec req;
  req.tv_nsec = 1000;
  req.tv_sec = 0;
  double diff;

  struct sched_param rt_param;
  int rt_max_prio = sched_get_priority_max(SCHED_FIFO);
  sched_getparam(getpid(), &rt_param);
  rt_param.sched_priority = rt_max_prio;
  sched_setscheduler(getpid(), SCHED_FIFO, &rt_param);

  printf("Raspberry Pi anemometer\n");
 
  if (wiringPiSetup () == -1) {
    return 1;
  }
 
  pinMode(8, INPUT);

  double first = 0;
  int pos = 0;
  int frame[50];
  int delay;
  int signal_freq = 1210;
  for (;;) {
    v = digitalRead(8);
    if( first > 0 && ((current_timestamp() - first) > 49300) ) {
      printf("\nNEW DATA FRAME usec:[%d] bits:[%d]:\n", (int)(current_timestamp() - first), pos);
      decode_frame(frame);
      first = 0;
      pos = 0;
    }
    // Waiting for signal
    delay = 120;
    if( first == 0 && v == 1 ) {
      first = current_timestamp();
      // Decoding, first time
      delay = signal_freq + signal_freq/2 - delay;
    }
    if( first > 0 ) {
      frame[pos++] = v;
      // Decoding
      delay = signal_freq;
    }

    diff = current_timestamp() - t2;
    while( diff < delay ) {
        nanosleep(&req, NULL);
        diff = current_timestamp() - t2;
    }
    t2 = current_timestamp();
    //printf("%f :[%d]\n", diff, v);
  }
  return 0;
}
