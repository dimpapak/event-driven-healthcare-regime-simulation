# Event-Driven Healthcare Regime Simulation

Python implementation accompanying the chapter:

**Event-Driven Stochastic Regime Shifts in Adaptive Healthcare Systems: Modelling Overload, Recovery, and Policy Response**

---

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

---

## Repository Structure

src/

├── simulate_healthcare_regimes.py

└── plot_igi_figures.py

---

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

---

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

---

## Software Availability

The Python implementation supporting the proposed event-driven healthcare regime framework has been made publicly available to improve transparency, reproducibility, and future research extensions.

---
## Citation

If you use this repository, please cite:

Papakyriakou, D. (2026).

Event-Driven Stochastic Regime Shifts in Adaptive Healthcare Systems:
Modelling Overload, Recovery, and Policy Response.

Book Chapter submitted to:
Stochastic Processes for Adaptive Healthcare Systems
(IGI Global Scientific Publishing).

## Author

Dimitrios Papakyriakou

PhD Candidate — Hellenic Mediterranean University

Independent Researcher in Neuromorphic Computing and Edge AI Systems

ORCID:
https://orcid.org/0000-0001-9745-0857
