# Event-Driven Healthcare Regime Simulation

**Version 1.0.0**

Python implementation accompanying the chapter:

**Event-Driven Stochastic Regime Shifts in Adaptive Healthcare Systems: Modelling Overload, Recovery, and Policy Response**

## Overview

This repository contains a discrete-event simulation framework for studying event-driven regime shifts in adaptive healthcare systems.

The framework models:

- Normal operation
- Demand surge events
- Overload regimes
- Policy intervention delays
- Recovery dynamics

The implementation combines:

- Queueing Theory (M/M/c)
- Event-Driven Simulation
- Adaptive Capacity Policies
- Regime-Based Dynamics

## Repository Structure

```text
src/
├── simulate_healthcare_regimes.py
└── plot_igi_figures.py

docs/
├── model_description.pdf
├── chapter_figures.pdf
└── README.md

sample_outputs/
├── event_log_example.csv
├── timeline_example.csv
├── results_summary.csv
├── fig1_timeline.png
├── fig2_heatmap_tover.png
├── fig3_recovery_vs_tau.png
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Run Simulation

```bash
python src/simulate_healthcare_regimes.py
```

## Generate Figures

```bash
python src/plot_igi_figures.py
```

## Outputs

The simulator generates:

- Event logs
- Timeline datasets
- Summary KPI tables
- Publication-quality figures

Key performance indicators include:

- Overload duration
- Recovery time
- Queue length
- Waiting time
- Throughput

Representative outputs are included in `sample_outputs/`.

## Reproducibility Note

The repository provides the implementation, model documentation, and representative outputs supporting the experimental workflow. The simulator uses a fixed base seed for experiment generation. Because replication-specific seeds are derived using Python's built-in `hash()` function, exact random streams may vary between independent Python processes or environments unless Python hash randomization is controlled. Accordingly, this release supports reproducibility of the modelling and experimental workflow but does not claim byte-for-byte identical stochastic outputs across all environments.

Recovery metrics should be interpreted within the finite simulation horizon used by the implementation; where recovery is not completed before the horizon, the reported value reflects the remaining horizon interval rather than an independently observed post-horizon recovery event.

## Software Availability

The Python implementation supporting the Event-Driven Healthcare Regime framework is publicly available to support transparency, reproducibility, and future research extensions.

Repository: https://github.com/dimpapak/event-driven-healthcare-regime-simulation

## Citation

### Software

Papakyriakou, D. (2026). *Event-Driven Healthcare Regime Simulation* (Version 1.0.0) [Computer software]. GitHub. https://github.com/dimpapak/event-driven-healthcare-regime-simulation

Machine-readable citation metadata are provided in `CITATION.cff`. The software DOI will be added after archival release in Zenodo.

### Associated Book Chapter

Papakyriakou, D. (2026). *Event-Driven Stochastic Regime Shifts in Adaptive Healthcare Systems: Modelling Overload, Recovery, and Policy Response*. In *Stochastic Processes for Adaptive Healthcare Systems*. IGI Global Scientific Publishing.

Chapter DOI: https://doi.org/10.4018/979-8-3373-9705-4.ch003

Book DOI: https://doi.org/10.4018/979-8-3373-9705-4

Publication status: Accepted and finalized (proofs completed October 2026). Projected release: December 2026.

## Author

Dimitrios Papakyriakou  
Independent Researcher in Neuromorphic Computing and Edge AI Systems  
ORCID: https://orcid.org/0000-0001-9745-0857

## License

This software is released under the MIT License. See `LICENSE`.
