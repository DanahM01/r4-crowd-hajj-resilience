"""
STEP 3a - Virtual sensors.

Each zone has a primary sensor: reading = true density + small random error.
For the redundancy mechanism each zone also has a backup sensor with its own
independent error. In the sensor-failure scenario the primary sensor of the
failed zone gives no reading (NaN) during the disruption.
"""
import numpy as np
import config as C


def read_sensors(true_density, rng, in_window, failed=()):
    shape = true_density.shape
    primary = np.clip(true_density + rng.normal(0, C.SENSOR_NOISE_SD, shape), 0, None)
    backup = np.clip(true_density + rng.normal(0, C.SENSOR_NOISE_SD, shape), 0, None)
    for z in failed:
        primary[in_window, z] = np.nan          # dead sensor: no reading at all
    return primary, backup
