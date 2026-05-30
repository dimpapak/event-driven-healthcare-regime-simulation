(venv) pi@rpi4B-ma-00:~/cloud $ cat simulate_healthcare_regimes.py
# simulate_healthcare_regimes.py
# Discrete-event simulation for event-driven regime shifts in an M/M/c queue
# Generates synthetic datasets: event logs, timelines, and KPI summary tables.

from __future__ import annotations

import heapq
import math
import os
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import csv

# -----------------------------
# Event and scenario definitions
# -----------------------------

ARRIVAL = "ARRIVAL"
DEPARTURE = "DEPARTURE"
REGIME_START = "REGIME_START"
REGIME_END = "REGIME_END"
POLICY_ACTION = "POLICY_ACTION"

@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    lambda0: float          # baseline arrival rate (per minute)
    mu: float               # service rate per server (per minute)
    c0: int                 # baseline number of servers
    surge_multiplier: float # s
    shock_start: float      # minutes
    shock_end: float        # minutes
    policy_lag: float       # tau (minutes)
    delta_c: int            # capacity increment
    nq_threshold: int       # overload detection threshold (queue length)


@dataclass
class PatientRec:
    patient_id: int
    arrival_time: float
    service_start_time: Optional[float] = None
    departure_time: Optional[float] = None
    service_time: Optional[float] = None
    regime_at_arrival: str = "normal"
    capacity_state_at_arrival: str = "baseline"
    queue_length_at_arrival: int = 0


@dataclass
class RunOutputs:
    # synthetic datasets
    event_log_rows: List[Dict]
    timeline_rows: List[Dict]
    # KPIs
    overload_duration: float
    recovery_time: float
    avg_wait: float
    max_nq: int
    throughput: float


# -----------------------------
# Utilities
# -----------------------------

def exp_sample(rate: float, rng: random.Random) -> float:
    """Sample from Exp(rate). If rate is 0, return +inf."""
    if rate <= 0:
        return float("inf")
    u = rng.random()
    return -math.log(1.0 - u) / rate


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


# -----------------------------
# Core DES simulator
# -----------------------------

def simulate_once(
    scenario: Scenario,
    horizon: float,
    seed: int,
    timeline_dt: float = 1.0,
    export_event_log: bool = True
) -> RunOutputs:
    rng = random.Random(seed)

    # State
    t = 0.0
    regime = "normal"
    lam = scenario.lambda0
    mu = scenario.mu
    c = scenario.c0
    policy_activated = False

    nq = 0
    ns = 0

    max_nq = 0

    # For waiting times, keep queue as list of patient_ids in FCFS order
    queue: List[int] = []

    patients: Dict[int, PatientRec] = {}
    next_patient_id = 0

    # Event list: (time, counter, event_type, payload)
    # counter avoids tie issues in heap ordering
    event_heap: List[Tuple[float, int, str, dict]] = []
    counter = 0

    def push_event(time: float, ev_type: str, payload: dict) -> None:
        nonlocal counter
        heapq.heappush(event_heap, (time, counter, ev_type, payload))
        counter += 1

    # schedule regime switch events
    push_event(scenario.shock_start, REGIME_START, {})
    push_event(scenario.shock_end, REGIME_END, {})

    # schedule first arrival
    next_arrival = t + exp_sample(lam, rng)
    push_event(next_arrival, ARRIVAL, {})

    # To track overload and recovery
    overload_intervals: List[Tuple[float, float]] = []
    overload_on = False
    overload_start_time = None

    shock_ended_time = None
    recovery_end_time = None

    # Time-series sampling
    timeline_rows: List[Dict] = []
    next_sample_time = 0.0

    # Event log rows
    event_log_rows: List[Dict] = []

    def current_rho() -> float:
        return lam / (max(c, 1) * mu)

    def update_overload_tracking(time_now: float) -> None:
        nonlocal overload_on, overload_start_time, recovery_end_time
        rho = current_rho()
        is_over = (rho >= 1.0) or (nq >= scenario.nq_threshold)

        if is_over and not overload_on:
            overload_on = True
            overload_start_time = time_now
        elif (not is_over) and overload_on:
            overload_on = False
            if overload_start_time is not None:
                overload_intervals.append((overload_start_time, time_now))
            overload_start_time = None

        # recovery end: after shock ended, first time system returns "below tolerance"
        if shock_ended_time is not None and recovery_end_time is None:
            below_tol = (nq == 0) and (current_rho() < 1.0)
            if below_tol:
                recovery_end_time = time_now

    def sample_timeline(time_now: float) -> None:
        timeline_rows.append({
            "time": round(time_now, 6),
            "Nq": nq,
            "Ns": ns,
            "c": c,
            "regime": regime,
            "lambda": lam,
            "rho": current_rho(),
            "policy_activated": int(policy_activated),
        })

    # Main loop
    while event_heap:
        time_now, _, ev_type, payload = heapq.heappop(event_heap)
        if time_now > horizon:
            break

        # sample timeline up to this event (regular dt)
        while next_sample_time <= time_now:
            # advance "virtual" time to sample point
            sample_timeline(next_sample_time)
            next_sample_time += timeline_dt

        t = time_now

        # Update overload tracking just before processing event at t
        update_overload_tracking(t)

        if ev_type == REGIME_START:
            regime = "overload"
            lam = scenario.lambda0 * scenario.surge_multiplier

        elif ev_type == REGIME_END:
            regime = "recovery"
            lam = scenario.lambda0
            shock_ended_time = t

        elif ev_type == POLICY_ACTION:
            # execute capacity adjustment once
            if not policy_activated:
                c = scenario.c0 + scenario.delta_c
                policy_activated = True

        elif ev_type == ARRIVAL:
            # create patient
            pid = next_patient_id
            next_patient_id += 1

            cap_state = "surged" if policy_activated else "baseline"
            patients[pid] = PatientRec(
                patient_id=pid,
                arrival_time=t,
                regime_at_arrival=regime,
                capacity_state_at_arrival=cap_state,
                queue_length_at_arrival=nq
            )

            if export_event_log:
                event_log_rows.append({
                    "time": t,
                    "event": "arrival",
                    "patient_id": pid,
                    "Nq": nq,
                    "Ns": ns,
                    "c": c,
                    "regime": regime,
                    "policy_activated": int(policy_activated),
                })

            # overload detection + schedule policy action
            rho = current_rho()
            overload_detected = (rho >= 1.0) or (nq >= scenario.nq_threshold)
            if overload_detected and (not policy_activated) and scenario.delta_c > 0:
                # schedule policy action if not already scheduled
                # (simple rule: schedule only once)
                push_event(t + scenario.policy_lag, POLICY_ACTION, {})

            # service immediately if server free
            if ns < c:
                ns += 1
                st = t
                svc_time = exp_sample(mu, rng)
                patients[pid].service_start_time = st
                patients[pid].service_time = svc_time
                dep_t = t + svc_time
                push_event(dep_t, DEPARTURE, {"patient_id": pid})

                if export_event_log:
                    event_log_rows.append({
                        "time": t,
                        "event": "service_start",
                        "patient_id": pid,
                        "Nq": nq,
                        "Ns": ns,
                        "c": c,
                        "regime": regime,
                        "policy_activated": int(policy_activated),
                    })
            else:
                # join queue
                nq += 1
                queue.append(pid)
                max_nq = max(max_nq, nq)

            # schedule next arrival
            next_arrival = t + exp_sample(lam, rng)
            push_event(next_arrival, ARRIVAL, {})

        elif ev_type == DEPARTURE:
            pid = payload["patient_id"]
            patients[pid].departure_time = t

            if export_event_log:
                event_log_rows.append({
                    "time": t,
                    "event": "departure",
                    "patient_id": pid,
                    "Nq": nq,
                    "Ns": ns,
                    "c": c,
                    "regime": regime,
                    "policy_activated": int(policy_activated),
                })

            # free a server
            ns -= 1
            if nq > 0:
                # take next from queue
                next_pid = queue.pop(0)
                nq -= 1
                ns += 1

                st = t
                svc_time = exp_sample(mu, rng)
                patients[next_pid].service_start_time = st
                patients[next_pid].service_time = svc_time
                dep_t = t + svc_time
                push_event(dep_t, DEPARTURE, {"patient_id": next_pid})

                if export_event_log:
                    event_log_rows.append({
                        "time": t,
                        "event": "service_start",
                        "patient_id": next_pid,
                        "Nq": nq,
                        "Ns": ns,
                        "c": c,
                        "regime": regime,
                        "policy_activated": int(policy_activated),
                    })

        # update overload tracking after event at t
        update_overload_tracking(t)

    # close overload interval if still on at horizon
    if overload_on and overload_start_time is not None:
        overload_intervals.append((overload_start_time, horizon))

    overload_duration = sum(b - a for a, b in overload_intervals)

    if shock_ended_time is None:
        recovery_time = 0.0
    else:
        if recovery_end_time is None:
            recovery_time = max(0.0, horizon - shock_ended_time)
        else:
            recovery_time = max(0.0, recovery_end_time - shock_ended_time)

    # waiting times
    waits = []
    completed = 0
    for p in patients.values():
        if p.departure_time is not None and p.service_start_time is not None:
            waits.append(p.service_start_time - p.arrival_time)
            completed += 1

    avg_wait = sum(waits) / len(waits) if waits else 0.0
    throughput = completed / horizon if horizon > 0 else 0.0

    return RunOutputs(
        event_log_rows=event_log_rows,
        timeline_rows=timeline_rows,
        overload_duration=overload_duration,
        recovery_time=recovery_time,
        avg_wait=avg_wait,
        max_nq=max_nq,
        throughput=throughput,
    )


# -----------------------------
# Batch runner and exporters
# -----------------------------

def run_experiments(
    out_dir: str = "out_igi_sim",
    replications: int = 10,
    horizon: float = 8 * 60.0,       # 8 hours in minutes
    lambda0: float = 0.9,            # arrivals per minute
    mu: float = 0.25,                # service rate per server per minute (mean service 4 min)
    c0: int = 4,
    shock_start: float = 60.0,
    shock_end: float = 180.0,
    nq_threshold: int = 10,
    s_values=(1.2, 1.5, 2.0),
    tau_values=(0.0, 15.0, 30.0, 60.0, 120.0),
    delta_c_values=(0, 1, 2),
    base_seed: int = 12345,
) -> None:
    ensure_dir(out_dir)

    summary_rows: List[Dict] = []

    # export one representative event log and timeline for illustration
    exported_example = False

    for s in s_values:
        for tau in tau_values:
            for dc in delta_c_values:
                scenario_id = f"s{s}_tau{int(tau)}_dc{dc}"
                scenario = Scenario(
                    scenario_id=scenario_id,
                    lambda0=lambda0,
                    mu=mu,
                    c0=c0,
                    surge_multiplier=s,
                    shock_start=shock_start,
                    shock_end=shock_end,
                    policy_lag=tau,
                    delta_c=dc,
                    nq_threshold=nq_threshold,
                )

                k_over, k_rec, k_wq, k_max, k_thr = [], [], [], [], []
                for r in range(replications):
                    seed = base_seed + hash((scenario_id, r)) % (10**7)
                    out = simulate_once(scenario, horizon=horizon, seed=seed, timeline_dt=1.0, export_event_log=True)

                    k_over.append(out.overload_duration)
                    k_rec.append(out.recovery_time)
                    k_wq.append(out.avg_wait)
                    k_max.append(out.max_nq)
                    k_thr.append(out.throughput)

                    # export one example dataset
                    if (not exported_example) and s == 1.5 and int(tau) == 60 and dc == 1 and r == 0:
                        # event log sample
                        with open(os.path.join(out_dir, "event_log_example.csv"), "w", newline="") as f:
                            w = csv.DictWriter(f, fieldnames=list(out.event_log_rows[0].keys()))
                            w.writeheader()
                            w.writerows(out.event_log_rows)

                        # timeline sample
                        with open(os.path.join(out_dir, "timeline_example.csv"), "w", newline="") as f:
                            w = csv.DictWriter(f, fieldnames=list(out.timeline_rows[0].keys()))
                            w.writeheader()
                            w.writerows(out.timeline_rows)

                        exported_example = True

                # aggregate
                def mean(xs): return sum(xs) / len(xs) if xs else 0.0

                summary_rows.append({
                    "scenario_id": scenario_id,
                    "s": s,
                    "tau": tau,
                    "delta_c": dc,
                    "mean_Tover": mean(k_over),
                    "mean_Trec": mean(k_rec),
                    "mean_Wq": mean(k_wq),
                    "mean_maxNq": mean(k_max),
                    "mean_throughput": mean(k_thr),
                    "replications": replications,
                })

    # write summary table
    summary_path = os.path.join(out_dir, "results_summary.csv")
    with open(summary_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)

    print(f"Wrote: {summary_path}")
    if exported_example:
        print(f"Wrote: {os.path.join(out_dir, 'event_log_example.csv')}")
        print(f"Wrote: {os.path.join(out_dir, 'timeline_example.csv')}")


if __name__ == "__main__":
    run_experiments()
(venv) pi@rpi4B-ma-00:~/cloud $
