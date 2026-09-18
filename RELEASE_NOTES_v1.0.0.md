# v1.0.0 — Initial Archival Release

Initial archival release of the Event-Driven Healthcare Regime Simulation software accompanying the chapter *Event-Driven Stochastic Regime Shifts in Adaptive Healthcare Systems: Modelling Overload, Recovery, and Policy Response*.

This release packages the existing scientific implementation together with model documentation, representative outputs, citation metadata, and reproducibility notes.

## Included

- Discrete-event healthcare regime simulator
- Figure-generation script
- Model documentation
- Representative event logs, timeline data, KPI summaries, and figures
- MIT License
- `CITATION.cff` metadata

## Scientific code integrity

The scientific source files in `src/` are unchanged from the pre-release baseline commit `54354e5`.

## Reproducibility scope

The release supports reproducibility of the modelling and experimental workflow. Exact stochastic random streams may vary between independent Python processes or environments because replication-specific seeds are derived using Python's built-in `hash()` function unless Python hash randomization is controlled.
