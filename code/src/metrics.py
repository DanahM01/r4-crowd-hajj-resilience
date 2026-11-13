"""
STEP 5 - Measures (one or more per R4 dimension).

All window measures use the SAME window: the disruption, seconds [start, end).

Robustness      : mae_disruption, availability, delivery_ratio, min_q (during the disruption)
Redundancy /
Resourcefulness : same measures, compared between mechanisms (RQ2)
Rapidity (RQ3)  : detection_s, response_from_start_s, response_after_detection_s,
                  outage_occurred, n_outages, mean_recovery_s, longest_outage_s,
                  seconds_below, post_recovery_s

Notes
- MAE ignores zone-seconds without a value, so it must be read together with availability and Q(t).
- availability = the operator SEES a value (fresh, held, backup or neighbour estimate).
  delivery_ratio = the primary MESSAGE arrived. A neighbour estimate fills the screen
  but does not recover the lost message, so the two can differ.
"""
import numpy as np
import config as C


def mae(est, truth, mask_t):
    """Mean |error| (persons/m2) over zone-seconds that HAVE a value. Missing values are not counted."""
    err = np.abs(est[mask_t] - truth[mask_t])
    return float(np.nanmean(err)) if np.any(~np.isnan(err)) else float("nan")


def availability(est, mask_t):
    """Share of zone-seconds where the control room showed ANY value."""
    return float(np.mean(~np.isnan(est[mask_t])))


def delivery_ratio(arrival, mask_t):
    """Share of primary messages measured in the window that reached the control room (late or not)."""
    return float(np.mean(arrival[mask_t] >= 0))


def quality_series(est, truth):
    """Q(t): share of zones that have a value AND |error| < ERROR_OK."""
    with np.errstate(invalid="ignore"):
        ok = (~np.isnan(est)) & (np.abs(est - truth) < C.ERROR_OK)
    return ok.mean(axis=1)


def detection(detected, start_s, end_s):
    """First second (and zone) in the window at which a zone's primary value becomes too old.
    detection_s = elapsed time t_detect - start. Example: a sensor silent from second 600 has a
    3 s old value at 602 (last reading 599), so detection_s = 2 s. NaN if never detected."""
    d = detected[start_s:end_s]
    rows = np.nonzero(d.any(axis=1))[0]
    if len(rows) == 0:
        return float("nan"), -1, -1
    t = start_s + int(rows[0])
    zone = int(np.argmax(detected[t]))
    return float(t - start_s), t, zone


def response(src, t_det, zone, start_s, end_s):
    """Response = first second a mechanism value (backup or neighbours) is shown.
    response_from_start_s : elapsed time from disruption start (same convention as detection_s).
    response_after_detection_s : seconds from detection to the first mechanism value in the
                                 SAME zone that was detected first.
    Both NaN when no mechanism value is ever shown (mechanism 'none', or the mechanism had no
    usable data)."""
    used = np.any(src[start_s:end_s] >= 3, axis=1)
    from_start = float(np.argmax(used)) if used.any() else float("nan")
    after = float("nan")
    if t_det >= 0:
        z_used = np.nonzero(src[t_det:end_s, zone] >= 3)[0]
        if len(z_used):
            after = float(z_used[0])
    return from_start, after


def outages(q, start_s, end_s):
    """Outages = runs of consecutive seconds with Q(t) < ACCEPTABLE_Q that START inside [start, end).
    An outage ends (the service RECOVERS) at the first second with Q(t) >= ACCEPTABLE_Q, even if
    that is after the disruption window; an outage still open at the end of the run is counted
    up to the end of the run.
    Returns (outage_occurred 0/1, number of outages, mean recovery time per outage in s,
    longest outage in s). When no outage happened the recovery times are NaN
    ("no outage"), not 0."""
    bad = q < C.ACCEPTABLE_Q
    lengths, t = [], start_s
    while t < end_s:
        if bad[t]:
            u = t
            while u < len(q) and bad[u]:
                u += 1
            lengths.append(u - t)
            t = u
        else:
            t += 1
    if not lengths:
        return 0, 0, float("nan"), float("nan")
    return 1, len(lengths), float(np.mean(lengths)), float(max(lengths))


def seconds_below(q, start_s, end_s):
    """Seconds in [start, end) with Q(t) below the acceptable level."""
    return int(np.sum(q[start_s:end_s] < C.ACCEPTABLE_Q))


def post_recovery(q, end_s):
    """Seconds from disruption end until Q(t) >= ACCEPTABLE_Q (0 = service acceptable at once).
    NaN if it never returns before the end of the run."""
    ok = np.nonzero(q[end_s:] >= C.ACCEPTABLE_Q)[0]
    return float(ok[0]) if len(ok) else float("nan")
