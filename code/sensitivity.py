"""
STEP 7 - Sensitivity analysis: do the conclusions change when the assumed values change?

One parameter is changed at a time; all others keep their main value from config.py.
  inflow_pps     : pilgrims entering per second      12, 18 (main)
  sensor_noise   : sensor noise SD (persons/m2)       0.1, 0.2 (main), 0.4
  error_ok       : tolerance for a zone to be OK      0.3, 0.5 (main), 1.0
  stale_after_s  : freshness limit (s)                2, 3 (main), 6
Every scenario and mechanism, 30 seeds each (same paired design as the main runs).

Outputs
  results/sensitivity_raw.csv        one row per run
  figures/table_sensitivity.csv      mean seconds below acceptable, availability, MAE
  figures/fig4_sensitivity.png       seconds below acceptable for each tested value

Run:  python sensitivity.py      (about 3 min)
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C
import run_experiments as R

PARAMS = {                                    # name in this table -> (name in config.py, values)
    "inflow_pps":    ("INFLOW_PPS",      [12.0, 18.0]),
    "sensor_noise":  ("SENSOR_NOISE_SD", [0.1, 0.2, 0.4]),
    "error_ok":      ("ERROR_OK",        [0.3, 0.5, 1.0]),
    "stale_after_s": ("STALE_AFTER_S",   [2, 3, 6]),
}
SCENARIOS = list(C.SCENARIOS)
SHORT = ["Base", "Sensor", "Loss10", "Loss30", "Loss50", "Delay2", "Delay5"]


def main():
    rows = []
    for pname, (cname, values) in PARAMS.items():
        main_value = getattr(C, cname)
        for v in values:
            setattr(C, cname, v)              # the modules read config values at run time
            for s in SCENARIOS:
                for m in C.MECHANISMS:
                    for seed in range(C.N_SEEDS):
                        row = R.run_one(s, m, seed)
                        row.update({"parameter": pname, "value": v, "is_main": v == main_value})
                        rows.append(row)
            print("done:", pname, v)
        setattr(C, cname, main_value)

    df = pd.DataFrame(rows)
    df.to_csv("results/sensitivity_raw.csv", index=False)
    tab = (df.groupby(["parameter", "value", "scenario", "mechanism"])
             [["seconds_below", "availability", "mae_disruption", "mean_true_density"]]
             .mean().round(4))
    tab.to_csv("figures/table_sensitivity.csv")

    fig, axs = plt.subplots(len(PARAMS), 3, figsize=(11, 2.4 * len(PARAMS)), sharey=True)
    x = np.arange(len(SCENARIOS))
    for r, (pname, (_, values)) in enumerate(PARAMS.items()):
        w = 0.8 / len(values)
        for c, m in enumerate(C.MECHANISMS):
            a = axs[r, c]
            for i, v in enumerate(values):
                y = [tab.loc[(pname, v, s, m), "seconds_below"] for s in SCENARIOS]
                a.bar(x + (i - (len(values) - 1) / 2) * w, y, w, label=f"{pname} = {v:g}")
            a.set_xticks(x); a.set_xticklabels(SHORT, fontsize=7)
            if r == 0:
                a.set_title(m, fontsize=9)
            if c == 0:
                a.set_ylabel("s with Q(t) < 90 %", fontsize=8)
            if c == 2:
                a.legend(fontsize=6, loc="upper left")
    fig.tight_layout(); fig.savefig("figures/fig4_sensitivity.png", dpi=200); plt.close(fig)
    print("saved figures/table_sensitivity.csv and figures/fig4_sensitivity.png")


if __name__ == "__main__":
    main()
