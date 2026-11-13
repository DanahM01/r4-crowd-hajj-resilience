"""
STEP 4 - Control room (monitor).

Works second by second, like a real dashboard. For each zone it keeps the NEWEST
message that has arrived so far (newest = most recent measurement time) and its
age = now - measurement time.

1. age == 0                     -> a fresh value is shown.
2. 0 < age < STALE_AFTER_S      -> the last value is still shown ("held": it was not
                                   refreshed, or it arrived late). The operator does
                                   not yet know that anything is wrong.
3. age >= STALE_AFTER_S         -> the value is too old and is NOT shown; the fault is
                                   DETECTED. Only now does the mechanism switch on:
     none        : no value (the zone is shown as "no data")
     redundancy  : the backup sensor of the same zone, if its value is younger than STALE_AFTER_S
     fallback    : mean of the neighbouring zones' primary values that are younger than STALE_AFTER_S

A late message is treated like any other: it is used if it is still younger than
STALE_AFTER_S when it arrives, otherwise it is ignored.

Returns
  est      : (T, Z) value shown to the operator (NaN = no data)
  src      : (T, Z) where the value came from: 0 none, 1 fresh, 2 held/late, 3 backup, 4 neighbours
  detected : (T, Z) True where the zone's primary value is too old (fault detected)
"""
import numpy as np
import config as C

NONE, FRESH, HELD, BACKUP, NEIGHBOURS = 0, 1, 2, 3, 4


def _newest(values, arrival):
    """Value shown from one stream (NaN if too old) and its age, for every second and zone."""
    T, Z = values.shape
    horizon = T + int(arrival.max(initial=0)) + 2
    best = np.full((horizon, Z), -1)
    s_idx, z_idx = np.nonzero(arrival >= 0)
    np.maximum.at(best, (arrival[s_idx, z_idx], z_idx), s_idx)     # newest measurement arriving at each second
    newest = np.maximum.accumulate(best, axis=0)[:T]                 # newest measurement known so far
    t = np.arange(T)[:, None]
    age = np.where(newest >= 0, t - newest, 10**6)
    val = values[np.clip(newest, 0, None), np.arange(Z)[None, :]]
    shown = np.where(age < C.STALE_AFTER_S, val, np.nan)
    return shown, age


def estimate(primary, arr_p, backup, arr_b, mechanism):
    prim, age = _newest(primary, arr_p)                      # steps 1 and 2
    est = prim.copy()
    src = np.where(age == 0, FRESH, np.where(~np.isnan(prim), HELD, NONE))
    detected = age >= C.STALE_AFTER_S                        # step 3

    if mechanism == "redundancy":
        back, _ = _newest(backup, arr_b)
        use = detected & ~np.isnan(back)
        est[use] = back[use]
        src[use] = BACKUP
    elif mechanism == "fallback":
        T, Z = prim.shape
        left = np.full((T, Z), np.nan)
        right = np.full((T, Z), np.nan)
        left[:, 1:] = prim[:, :-1]
        right[:, :-1] = prim[:, 1:]
        n = (~np.isnan(left)).astype(int) + (~np.isnan(right)).astype(int)
        total = np.nan_to_num(left) + np.nan_to_num(right)
        neigh = np.where(n > 0, total / np.maximum(n, 1), np.nan)
        use = detected & ~np.isnan(neigh)
        est[use] = neigh[use]
        src[use] = NEIGHBOURS
    return est, src, detected
