"""
All fixed settings of the simulation in one place.
Every number here is reported (and justified) in the Methodology section.
"""

# ---------- Space ----------
N_ZONES = 6                          # corridor towards the Jamarat split into 6 zones
ZONE_LENGTH_M = 10.0                 # each zone is 10 m long (walking direction)
# The corridor narrows towards the Jamarat entrance (a bottleneck), so the
# last zones are more crowded than the first ones. Width in metres per zone.
ZONE_WIDTHS_M = [20.0, 20.0, 20.0, 19.0, 18.0, 17.0]

# ---------- Time ----------
DT_S = 1.0                           # one step = 1 s (sensors report every second)
DURATION_S = 30 * 60                 # 30 min = 1800 steps
DISRUPTION_START_S = 10 * 60         # disruption starts at minute 10
DISRUPTION_END_S = 15 * 60           # and ends at minute 15
WARMUP_S = 120                       # inflow ramps up over the first 2 minutes

# ---------- Crowd calibration: Johansson et al. (2008), Jamarat, Fig. 14 / Eq. 14 ----------
V0_MS = 0.60                         # free walking speed of pilgrims (m/s)
RHO_MAX = 10.79                      # density at which movement stops (persons/m2)
GAMMA = 0.35                         # constant in V = V0 * (1 - exp(-GAMMA * (RHO_MAX/rho - 1)))
INFLOW_PPS = 18.0                    # pilgrims entering zone 1 per second (after warm-up)
INFLOW_NOISE = 0.10                  # inflow each second = INFLOW_PPS * (1 + 0.10 * N(0,1)): Gaussian, relative SD 10 %

# ---------- Sensors ----------
SENSOR_NOISE_SD = 0.2                # assumed measurement noise (persons/m2), Gaussian
FAILED_SENSORS = [4]                 # zone index that fails in "sensor_failure" (index 4 = zone 5, near the bottleneck)

# ---------- Scenarios: name -> (type, severity) ----------
SCENARIOS = {
    "baseline":       ("none",   0.0),
    "sensor_failure": ("sensor", 1.0),
    "packet_loss_10": ("loss",   0.10),
    "packet_loss_30": ("loss",   0.30),
    "packet_loss_50": ("loss",   0.50),
    "delay_2":        ("delay",  2),     # every message sent during the disruption arrives 2 s late
    "delay_5":        ("delay",  5),     # every message sent during the disruption arrives 5 s late
}
# Delay scenarios: a fixed extra delay for ALL messages (primary and backup, all zones), as in
# network-wide congestion. Messages keep their order. Each message carries the time it was measured,
# so the monitor knows how old a value is (age = now - measurement time).
MECHANISMS = ["none", "redundancy", "fallback"]

# ---------- Repetition ----------
N_SEEDS = 30

# ---------- Service quality ----------
ERROR_OK = 0.5                       # a zone is OK if it has a value and |error| < 0.5 person/m2.
                                     # Was 1.0 (= 5 x noise SD), which almost no reading ever exceeds, so Q(t) only
                                     # measured availability. 0.5 (= 2.5 x noise SD) makes Q(t) reflect accuracy too.
                                     # 0.3 and 1.0 are tested in sensitivity.py.
ACCEPTABLE_Q = 0.90                  # service acceptable when Q(t) >= 90 % (with 6 zones: all 6 OK)
STALE_AFTER_S = 3                    # a value is usable while its age < 3 s. When the newest value of a zone is
                                     # 3 s old (lost, failed or late messages) the fault is DETECTED and the
                                     # mechanism (if any) switches on; values aged >= 3 s are never shown.

# ---------- Recovery (RQ3) ----------
# Outage   = a run of consecutive seconds inside the disruption window with Q(t) < ACCEPTABLE_Q.
# Recovery = the outage ends at the first second with Q(t) >= ACCEPTABLE_Q again;
#            recovery time = outage start -> that second (= outage length).
# Post-disruption recovery = seconds from disruption end until Q(t) >= ACCEPTABLE_Q
#            (sensors and network are restored instantly at the end in this model, an assumption).
