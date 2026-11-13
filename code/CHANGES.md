# Changes after instructor feedback (12 Nov 2026)

1. config.py: ERROR_OK 1.0 -> 0.5 p/m2. With 1.0 (= 5 x sensor noise SD) almost no reading fails, so Q(t) measured availability only. With 0.5 (= 2.5 x SD), Q(t) also reflects accuracy.
2. make_figures.py: tests_rq2.csv now also compares backup vs neighbour estimate directly (paired Wilcoxon, Holm over all 54 tests).
3. sensitivity.py: one parameter at a time, all scenarios x mechanisms x 30 seeds:
   inflow 12/18, sensor noise 0.1/0.2/0.4, tolerance 0.3/0.5/1.0, freshness limit 2/3/6 s.
4. README.md updated. Everything re-run: results/ and figures/ are new.
No change to the crowd model, sensors, channel or monitor.
