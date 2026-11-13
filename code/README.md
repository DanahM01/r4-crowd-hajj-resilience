# G4 Phase 3: Resilience of a simulated Hajj crowd-monitoring CPS (R4 framework)

## How to run (Windows / Mac / Linux, Python 3.9+)
```
pip install -r requirements.txt
python run_experiments.py     # ~20 s, writes results/raw_results.csv (630 runs)
python make_figures.py        # writes tables and figures to figures/
python sensitivity.py         # sensitivity: inflow, sensor noise, tolerance, freshness (~3 min)
```
The same seeds always give the same numbers, so anyone can reproduce the results.

## Structure
| File | What it does |
|---|---|
| config.py | all settings: corridor, time, calibration, scenarios, seeds, thresholds |
| src/crowd.py | true density per zone per second (speed-density relation of Johansson et al., 2008) |
| src/sensors.py | primary and backup sensor readings with noise; failed sensor gives no reading |
| src/channel.py | when each message arrives: independent packet loss (a simplified proxy for jamming) or a fixed 2 s / 5 s delay during the disruption |
| src/monitor.py | control-room dashboard: shows the newest value that is younger than 3 s (fresh, held or late); when a zone's newest value is 3 s old the fault is detected and none / redundancy (backup) / fallback (neighbours) is applied |
| src/metrics.py | MAE, availability, delivery ratio, Q(t), detection, response (from start and after detection), outages and recovery time, seconds below acceptable, post-disruption recovery. All window measures use the disruption window 600-900 s |
| run_experiments.py | 7 scenarios (baseline, sensor failure, loss 10/30/50 %, delay 2/5 s) x 3 mechanisms x 30 seeds |
| make_figures.py | tables (CSV), figures (PNG), paired Wilcoxon signed-rank tests with Holm correction, plausibility check of the crowd model |
| sensitivity.py | re-runs everything changing one value at a time (inflow, sensor noise, tolerance, freshness limit) |

## Data
All data are synthetic; no pilgrim data were collected. Crowd parameters come from
A. Johansson, D. Helbing, H. Z. Al-Abideen and S. Al-Bosta, "From crowd dynamics to crowd safety:
A video-based analysis," Advances in Complex Systems, 11(4), 497-527, 2008.
Results describe this model, not a deployed Hajj system. The crowd-model check compares the
model with published values only (a plausibility check, not a validation with real data).

## Definitions used in the results
- Acceptable service: Q(t) >= 90 % (all 6 zones show a value with error < 0.5 person/m2).
- Detection: elapsed time from disruption start until a zone's newest value is 3 s old
  (a sensor silent from 600 s is detected at 602 s -> 2 s; its last value is then 3 s old).
- Response: seconds from detection to the first backup/neighbour value in the same zone.
- Denominators: outages per run = all 30 runs; recovery per outage = all outages in the runs that had one;
  detection/response means = only the runs where detection/response happened (counts in table_rq3.csv).
- Outage: consecutive seconds with Q(t) < 90 % starting during the disruption; recovery time = outage
  start until Q(t) >= 90 % again (followed past the end of the disruption if needed).
  Runs without any outage are reported as "no outage", not as 0 s.
- Post-disruption recovery: seconds from the end of the disruption until Q(t) >= 90 %. It is 0 s
  because sensors and network are restored instantly in the model (an assumption).
