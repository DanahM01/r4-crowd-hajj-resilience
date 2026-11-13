"""
STEP 5 - Run every scenario x mechanism x seed and save the raw results.

Outputs
  results/raw_results.csv   one row per run (7 scenarios x 3 mechanisms x 30 seeds = 630 rows)
  results/q_series.csv      Q(t) of seed 0 for every scenario/mechanism (for the RQ3 figure)
  results/truth_seed0.csv   true density of seed 0 (to check the crowd model)

Run:  python run_experiments.py
"""
import numpy as np
import pandas as pd
import config as C
from src import crowd, sensors, channel, monitor, metrics


def run_one(scenario, mechanism, seed, keep_series=False):
    kind, severity = C.SCENARIOS[scenario]
    # The same seed gives the SAME crowd and the SAME random events for every mechanism,
    # so the mechanisms are compared on identical conditions (paired design).
    rng = np.random.default_rng(seed)
    truth = crowd.generate_true_density(rng)
    T = truth.shape[0]
    t = np.arange(T)
    win = (t >= C.DISRUPTION_START_S) & (t < C.DISRUPTION_END_S)

    failed = C.FAILED_SENSORS if kind == "sensor" else ()
    primary, backup = sensors.read_sensors(truth, rng, win, failed)
    loss = severity if kind == "loss" else 0.0
    delay = int(severity) if kind == "delay" else 0
    arr_p = channel.transmit(primary, rng, win, loss_rate=loss, delay_s=delay)
    arr_b = channel.transmit(backup, rng, win, loss_rate=loss, delay_s=delay)
    est, src, detected = monitor.estimate(primary, arr_p, backup, arr_b, mechanism)

    S, E = C.DISRUPTION_START_S, C.DISRUPTION_END_S
    q = metrics.quality_series(est, truth)
    det_s, t_det, z_det = metrics.detection(detected, S, E)
    resp_start, resp_after = metrics.response(src, t_det, z_det, S, E)
    occurred, n_out, mean_rec, max_out = metrics.outages(q, S, E)
    row = {
        "scenario": scenario, "mechanism": mechanism, "seed": seed,
        "mae_disruption": metrics.mae(est, truth, win),
        "availability": metrics.availability(est, win),
        "delivery_ratio": metrics.delivery_ratio(arr_p, win),
        "min_q": float(q[win].min()),
        "held_share": float(np.mean(src[win] == monitor.HELD)),
        "detection_s": det_s,
        "response_from_start_s": resp_start,
        "response_after_detection_s": resp_after,
        "outage_occurred": occurred,
        "n_outages": n_out,
        "mean_recovery_s": mean_rec,
        "longest_outage_s": max_out,
        "seconds_below": metrics.seconds_below(q, S, E),
        "post_recovery_s": metrics.post_recovery(q, E),
        "mean_true_density": float(truth[win].mean()),
    }
    return (row, q, truth) if keep_series else row


def main():
    rows, series = [], {}
    for scenario in C.SCENARIOS:
        for mechanism in C.MECHANISMS:
            for seed in range(C.N_SEEDS):
                if seed == 0:
                    row, q, truth = run_one(scenario, mechanism, seed, keep_series=True)
                    series[f"{scenario}|{mechanism}"] = q
                    if scenario == "baseline" and mechanism == "none":
                        pd.DataFrame(truth, columns=[f"zone_{i+1}" for i in range(C.N_ZONES)]).to_csv(
                            "results/truth_seed0.csv", index_label="t_s")
                else:
                    row = run_one(scenario, mechanism, seed)
                rows.append(row)
        print("done:", scenario)
    pd.DataFrame(rows).to_csv("results/raw_results.csv", index=False)
    pd.DataFrame(series).to_csv("results/q_series.csv", index_label="t_s")
    print("saved", len(rows), "runs to results/raw_results.csv")


if __name__ == "__main__":
    main()
