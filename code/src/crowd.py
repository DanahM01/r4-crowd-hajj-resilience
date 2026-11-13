"""
STEP 2 - Ground-truth crowd density.

Pilgrims enter zone 1 and walk zone by zone to the exit (the Jamarat side).
Every second we move people forward. How many can move depends on how crowded
the zone is (speed-density relation of Johansson et al., 2008) and on how much
free space the next zone has.

Output: array (T, N_ZONES) with the TRUE density (persons/m2). The monitoring
system never sees this array; we only use it to measure errors.
"""
import numpy as np
import config as C

WIDTHS = np.array(C.ZONE_WIDTHS_M)
AREAS = WIDTHS * C.ZONE_LENGTH_M
CAPACITY = 0.98 * C.RHO_MAX * AREAS          # max people a zone can hold


def speed(rho):
    """Walking speed (m/s) for density rho (persons/m2). Works on arrays."""
    rho = np.asarray(rho, dtype=float)
    v = np.full_like(rho, C.V0_MS)                       # empty zone -> free speed
    busy = rho > 0
    v[busy] = C.V0_MS * (1 - np.exp(-C.GAMMA * (C.RHO_MAX / rho[busy] - 1)))
    v[rho >= C.RHO_MAX] = 0.0                            # full zone -> nobody moves
    return np.clip(v, 0.0, C.V0_MS)


def inflow(t, rng):
    """Pilgrims entering zone 1 at second t: ramps up, then constant with Gaussian noise (relative SD 10 %)."""
    ramp = min(1.0, t / C.WARMUP_S)
    return max(0.0, C.INFLOW_PPS * ramp * (1 + C.INFLOW_NOISE * rng.normal()))


def generate_true_density(rng):
    T = int(C.DURATION_S / C.DT_S)
    people = np.zeros(C.N_ZONES)
    density = np.zeros((T, C.N_ZONES))
    for t in range(T):
        rho = people / AREAS
        # 1) how many WANT to leave each zone: flow = density * speed * width
        out = np.minimum(people, rho * speed(rho) * WIDTHS * C.DT_S)
        # 2) they can only enter the next zone if there is space
        out[:-1] = np.minimum(out[:-1], np.maximum(0.0, CAPACITY[1:] - people[1:]))
        # 3) new pilgrims at the entrance (also limited by space)
        new = min(inflow(t, rng), max(0.0, CAPACITY[0] - people[0]))
        # 4) move everybody (the last zone's outflow leaves the corridor)
        people -= out
        people[1:] += out[:-1]
        people[0] += new
        density[t] = people / AREAS
    return density
