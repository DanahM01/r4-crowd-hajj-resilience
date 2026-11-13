"""
STEP 3b - Communication channel.

Each reading is a message that carries its value and the second it was measured.
The channel decides WHEN (or whether) each message reaches the control room.

  loss  : during the disruption window each message is lost independently with
          probability loss_rate (a simplified PROXY for wireless jamming; it is not
          a model of real radio interference or of bursty loss).
  delay : during the disruption window every message arrives `delay_s` seconds late
          (fixed delay, same for all sensors, order is kept).

Returns arrival[t, z] = second at which the message measured at second t arrives,
or -1 if it never arrives (lost, or no reading because the sensor failed).
"""
import numpy as np


def transmit(readings, rng, in_window, loss_rate=0.0, delay_s=0):
    T, Z = readings.shape
    arrival = np.repeat(np.arange(T)[:, None], Z, axis=1)
    if delay_s > 0:
        arrival[in_window] += int(delay_s)
    if loss_rate > 0:
        lost = rng.random(readings.shape) < loss_rate
        lost &= in_window[:, None]               # loss only during the disruption
        arrival[lost] = -1
    arrival[np.isnan(readings)] = -1             # failed sensor: nothing is sent
    return arrival
