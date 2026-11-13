"""
STEP 6 - Tables, figures and statistical tests from the saved results.

Outputs (in figures/)
  table_plausibility_check.csv  plausibility check of the crowd model against published values
                           (Johansson et al., 2008); NOT a validation with real data
  table_rq1.csv            RQ1: the system WITHOUT mechanisms during each disruption
  table_rq2.csv            RQ2: every scenario x mechanism (mean and 95 % CI over 30 seeds)
  table_rq3.csv            RQ3: detection, response, outages and recovery, seconds below acceptable
  tests_rq2.csv            paired Wilcoxon signed-rank tests (none vs each mechanism, and backup vs
                           neighbour estimate), Holm-corrected over all tests
  fig0_crowd.png           true density per zone over time (model check)
  fig1_rq1.png             RQ1: availability and seconds below acceptable, no mechanism
  fig2_rq2.png             RQ2: seconds below acceptable per scenario and mechanism
  fig3_rq3.png             RQ3: Q(t) around the disruption (seed 0)

Run:  python make_figures.py
"""
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
import config as C
from src import crowd

warnings.simplefilter("ignore", category=FutureWarning)
df = pd.read_csv("results/raw_results.csv")
SC = list(C.SCENARIOS)
ME = C.MECHANISMS
MEASURES = ["availability", "delivery_ratio", "mae_disruption", "min_q", "held_share",
            "detection_s", "response_from_start_s", "response_after_detection_s",
            "outage_occurred", "n_outages", "mean_recovery_s", "longest_outage_s",
            "seconds_below", "post_recovery_s"]
# Conditional measures: the mean is taken ONLY over runs where the event happened
# (pandas skips NaN). detected_runs / runs_with_outage / responded_runs give how many runs that is.
# Denominators in table_rq3.csv: n_outages_mean = all 30 runs; n_outages_in_runs_with_outage = runs
# with an outage; mean_recovery_s_mean = mean over runs with an outage of each run's mean outage length.
LABEL = {"baseline": "Baseline", "sensor_failure": "Sensor failure",
         "packet_loss_10": "Loss 10%", "packet_loss_30": "Loss 30%", "packet_loss_50": "Loss 50%", "delay_2": "Delay 2 s", "delay_5": "Delay 5 s"}
MLABEL = {"none": "No mechanism", "redundancy": "Redundancy (backup sensor)",
          "fallback": "Resourcefulness (neighbour estimate)"}


def ci95(x):
    x = pd.Series(x).dropna()
    if len(x) < 2:
        return np.nan
    return float(stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)))


def summary(g):
    out = {}
    for m in MEASURES:
        out[m + "_mean"] = g[m].mean()
        out[m + "_ci95"] = ci95(g[m])
    out["detected_runs"] = int(g["detection_s"].notna().sum())
    out["responded_runs"] = int(g["response_after_detection_s"].notna().sum())
    out["runs_with_outage"] = int(g["outage_occurred"].sum())
    hit = g[g["outage_occurred"] == 1]["n_outages"]
    out["n_outages_in_runs_with_outage"] = hit.mean() if len(hit) else np.nan
    out["n"] = len(g)
    return pd.Series(out)


tab = df.groupby(["scenario", "mechanism"]).apply(summary).reindex(
    pd.MultiIndex.from_product([SC, ME], names=["scenario", "mechanism"]))
tab.round(4).to_csv("figures/table_rq2.csv")
r1 = tab.xs("none", level="mechanism")
r1[["availability_mean", "availability_ci95", "delivery_ratio_mean", "mae_disruption_mean",
    "mae_disruption_ci95", "min_q_mean", "seconds_below_mean", "seconds_below_ci95"]].round(4).to_csv("figures/table_rq1.csv")
tab[["detected_runs", "detection_s_mean", "detection_s_ci95",
     "responded_runs", "response_from_start_s_mean", "response_after_detection_s_mean",
     "runs_with_outage", "n_outages_mean", "n_outages_in_runs_with_outage", "mean_recovery_s_mean", "mean_recovery_s_ci95",
     "longest_outage_s_mean", "seconds_below_mean", "seconds_below_ci95",
     "post_recovery_s_mean"]].round(2).to_csv("figures/table_rq3.csv")

# ---- Plausibility check against published values (Johansson et al., 2008); not a validation ----
truth = pd.read_csv("results/truth_seed0.csv", index_col="t_s")
steady = truth.loc[5 * 60:]                                   # after warm-up
rho = steady.mean().values
v = crowd.speed(rho)
flow_per_m = rho * v                                          # persons per metre per second
check = pd.DataFrame({
    "zone": [f"zone {i+1}" for i in range(C.N_ZONES)],
    "width_m": C.ZONE_WIDTHS_M,
    "mean_density_p_m2": rho.round(2),
    "max_density_p_m2": steady.max().values.round(2),
    "speed_m_s": v.round(3),
    "flow_p_per_m_s": flow_per_m.round(3),
    "below_4_p_m2_limit": steady.max().values < 4,
})
check.to_csv("figures/table_plausibility_check.csv", index=False)

# ---- RQ2 tests: paired by seed, Holm correction ----
# none vs each mechanism, AND backup vs neighbour estimate directly.
PAIRS = [("none", "redundancy"), ("none", "fallback"), ("redundancy", "fallback")]
tests = []
for s in SC:
    if s == "baseline":
        continue
    for m1, m2 in PAIRS:
        first = df[(df.scenario == s) & (df.mechanism == m1)].sort_values("seed")
        second = df[(df.scenario == s) & (df.mechanism == m2)].sort_values("seed")
        for measure in ["seconds_below", "availability", "mae_disruption"]:
            a, b = first[measure].values, second[measure].values
            diff = b - a
            p = 1.0 if np.allclose(diff, 0) else stats.wilcoxon(a, b).pvalue
            tests.append({"scenario": s, "comparison": f"{m1} vs {m2}", "measure": measure,
                          "mean_first": a.mean(), "mean_second": b.mean(),
                          "mean_difference": diff.mean(), "ci95_difference": ci95(diff), "p_value": p})
tests = pd.DataFrame(tests)
order = np.argsort(tests.p_value.values)                       # Holm-Bonferroni
m_tests = len(tests)
adj = np.empty(m_tests)
running = 0.0
for rank, idx in enumerate(order):
    running = max(running, min(1.0, (m_tests - rank) * tests.p_value.values[idx]))
    adj[idx] = running
tests["p_holm"] = adj
tests["significant_0.05"] = tests.p_holm < 0.05
tests.to_csv("figures/tests_rq2.csv", index=False, float_format="%.4g")

# ---- Fig 0: crowd model check ----
fig, ax = plt.subplots(figsize=(7, 3.2))
for c in truth.columns:
    ax.plot(truth.index / 60, truth[c], label=c.replace("_", " "))
ax.axhline(4, ls=":", c="grey")
ax.text(0.3, 3.75, "recommended limit 4 p/m² (Johansson et al., 2008)", fontsize=8, color="grey")
ax.set_xlabel("Time (min)"); ax.set_ylabel("True density (persons/m²)")
ax.legend(ncol=3, fontsize=8); fig.tight_layout(); fig.savefig("figures/fig0_crowd.png", dpi=200); plt.close(fig)

# ---- Fig 1: RQ1 ----
fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
x = np.arange(len(SC))
axs[0].bar(x, r1["availability_mean"] * 100, yerr=r1["availability_ci95"] * 100, capsize=3)
axs[0].set_ylabel("Zone-seconds with a value (%)"); axs[0].set_ylim(0, 105)
axs[1].bar(x, r1["seconds_below_mean"], yerr=r1["seconds_below_ci95"], capsize=3, color="tab:red")
axs[1].set_ylabel("Seconds with Q(t) < 90 %")
for a in axs:
    a.set_xticks(x); a.set_xticklabels([LABEL[s] for s in SC], rotation=30, ha="right", fontsize=8)
fig.suptitle("RQ1: system without mechanisms (mean of 30 seeds, 95 % CI)", fontsize=10)
fig.tight_layout(); fig.savefig("figures/fig1_rq1.png", dpi=200); plt.close(fig)

# ---- Fig 2: RQ2 ----
fig, ax = plt.subplots(figsize=(9.5, 3.6))
w = 0.27
for i, m in enumerate(ME):
    d = tab.xs(m, level="mechanism")
    ax.bar(x + (i - 1) * w, d["seconds_below_mean"], w, yerr=d["seconds_below_ci95"], capsize=2, label=MLABEL[m])
ax.set_xticks(x); ax.set_xticklabels([LABEL[s] for s in SC], fontsize=8)
ax.set_ylabel("Seconds with Q(t) < 90 %"); ax.legend(fontsize=8)
ax.set_title("RQ2: effect of the mechanisms (mean of 30 seeds, 95 % CI)", fontsize=10)
fig.tight_layout(); fig.savefig("figures/fig2_rq2.png", dpi=200); plt.close(fig)

# ---- Fig 3: RQ3 ----
qs = pd.read_csv("results/q_series.csv", index_col="t_s")
fig, axs = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
for a, s in zip(axs, ["sensor_failure", "packet_loss_50"]):
    for m in ME:
        a.step(qs.index / 60, qs[f"{s}|{m}"] * 100, where="post", label=MLABEL[m], lw=1)
    a.axvspan(C.DISRUPTION_START_S / 60, C.DISRUPTION_END_S / 60, color="red", alpha=0.08)
    a.axhline(C.ACCEPTABLE_Q * 100, ls="--", c="green", lw=0.8)
    a.set_title(LABEL[s] + " (seed 0)", fontsize=10); a.set_xlabel("Time (min)")
axs[0].set_xlim(9.9, 10.5); axs[0].set_title("Sensor failure, first 36 s (seed 0)", fontsize=10)
axs[1].set_xlim(9.5, 15.5)
axs[0].set_ylabel("Q(t) (%)"); axs[0].legend(fontsize=7, loc="lower right")
fig.tight_layout(); fig.savefig("figures/fig3_rq3.png", dpi=200); plt.close(fig)

print("Tables and figures saved in figures/")
