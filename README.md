# R4 Crowd: Resilience of a Hajj Crowd-Monitoring System (R4 Framework)

SW 350 Undergraduate Scientific Research. Group G4, section O51, Department of Software Engineering, Princess Nourah bint Abdulrahman University.
Team: Leena Alshehri, Danah Alsaif, Layan Alshehri, Reef Albadrani.

This repository holds everything needed to reproduce the study: the simulation code, the raw data it produced, the figures and tables used in the paper, and the interactive demo shown at the Ofoq exhibition.

**Live demo:** https://r4-crowd-hajj-resilience-demo.vercel.app

## Contents

| Folder | What it holds |
|---|---|
| `code/` | Python simulation (crowd model, sensors, channel, monitor, metrics) and experiment scripts; see `code/README.md`. Changes made after the instructor's Phase 3 feedback are listed in `code/CHANGES.md` |
| `code/results/` | Raw outputs: `raw_results.csv` (630 runs = 7 scenarios x 3 mechanisms x 30 seeds), `q_series.csv`, `sensitivity_raw.csv`, `truth_seed0.csv` |
| `code/figures/` | Figures (`fig0`–`fig4`) and tables (CSV) for RQ1, RQ2, RQ3, plausibility check and sensitivity, plus paired Wilcoxon tests (`tests_rq2.csv`) |
| `demo/index.html` | Interactive explainer. Open it in any web browser; no install needed |
| `paper/` | Final paper (PDF), added after submission |

## Research questions
- **RQ1 (Robustness):** to what extent does the system keep density accuracy and data availability during sensor failure, packet loss and delay?
- **RQ2 (Redundancy, Resourcefulness):** how much do a backup sensor and a neighbour-zone estimate reduce data loss and error, compared with no mechanism?
- **RQ3 (Rapidity):** how quickly does the system detect, respond to and recover from the disruption?

## Reproducing the results
Requires Python 3.9 or later.
```
cd code
pip install -r requirements.txt
python run_experiments.py   # about 20 s, writes results/raw_results.csv
python make_figures.py      # writes tables, tests and figures to figures/
python sensitivity.py       # about 3 min, one parameter at a time
```
Fixed seeds are used, so the same commands give the same numbers.

## Model in brief
- Corridor of 6 zones (widths 20, 20, 20, 19, 18, 17 m), inflow 18 pilgrims/s, Cell Transmission Model (Daganzo, 1994).
- Speed-density relation calibrated to Jamarat data: Johansson et al. (2008), V0 = 0.60 m/s, rho_max = 10.79 p/m².
- Sensor noise SD 0.2 p/m². A zone is correct when it shows a value within 0.5 p/m² of the true density; the service is acceptable when all 6 zones are correct.
- Disruption window 600–900 s: sensor in zone 5 fails, packet loss of 10/30/50 %, or a fixed message delay of 2 s or 5 s.
- The monitor shows the newest value younger than 3 s; when it is 3 s old the zone is marked faulty and one mechanism is applied: none, redundancy (backup sensor) or fallback (neighbouring zones).
- Mechanisms are compared on the same seeds with paired Wilcoxon signed-rank tests, Holm-corrected over all 54 tests (including backup vs neighbour estimate).
- Sensitivity: inflow (12, 18), sensor noise (0.1, 0.2, 0.4), tolerance (0.3, 0.5, 1.0) and freshness limit (2, 3, 6 s), one at a time.

## Main result
Seconds below acceptable service during the 300 s disruption (mean of 30 seeds; noise alone gives 21.2 s):

| Scenario | No mechanism | Backup sensor | Neighbour estimate |
|---|---|---|---|
| Sensor failure | 298.2 | 21.0 | 18.0 |
| 50 % packet loss | 172.4 | 47.2 | 41.9 |
| 5 s delay | 298.2 | 298.2 | 298.2 |

## About the demo
The demo is a simplified JavaScript copy of the simulation, made for explaining the study to visitors. It follows the same rules, but the official numbers are the ones produced by the Python code in `code/`.

## Data
All data are synthetic. No data about real pilgrims were collected. Results describe this model, not a deployed Hajj system. The crowd model is checked for plausibility against published values, not validated with real data. Packet loss is independent per message and is not evidence of resistance to real jamming. Limitations are discussed in the paper.
