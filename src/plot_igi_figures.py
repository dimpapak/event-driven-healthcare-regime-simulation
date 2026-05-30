# plot_igi_figures.py
# Matplotlib-only plotting for IGI chapter figures:
# Figure 1: timeline + queue length + capacity + regime shading
# Figure 2: heatmap of overload duration across (tau, s) (optionally for fixed delta_c)
# Figure 3: recovery time vs tau for different delta_c (optionally for fixed s)

from __future__ import annotations

import os
import math
import csv
from typing import Dict, List, Tuple

import numpy as np
import matplotlib.pyplot as plt


OUT_DIR = "out_igi_sim"
FIG_DIR = os.path.join(OUT_DIR, "figures")

TIMELINE_CSV = os.path.join(OUT_DIR, "timeline_example.csv")
SUMMARY_CSV = os.path.join(OUT_DIR, "results_summary.csv")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", newline="") as f:
        return list(csv.DictReader(f))


def to_float(x: str) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")


def to_int(x: str) -> int:
    try:
        return int(float(x))
    except Exception:
        return 0


def plot_figure_1_timeline(timeline_csv: str, out_path: str) -> None:
    rows = read_csv(timeline_csv)

    t = np.array([to_float(r["time"]) for r in rows], dtype=float)
    nq = np.array([to_int(r["Nq"]) for r in rows], dtype=int)
    ns = np.array([to_int(r["Ns"]) for r in rows], dtype=int)
    c = np.array([to_int(r["c"]) for r in rows], dtype=int)
    rho = np.array([to_float(r["rho"]) for r in rows], dtype=float)
    regime = [r["regime"] for r in rows]
    policy = np.array([to_int(r.get("policy_activated", "0")) for r in rows], dtype=int)

    segments: List[Tuple[int, int, str]] = []
    start = 0
    for i in range(1, len(regime)):
        if regime[i] != regime[i - 1]:
            segments.append((start, i - 1, regime[i - 1]))
            start = i
    segments.append((start, len(regime) - 1, regime[-1]))

    fig = plt.figure(figsize=(11, 7.5))
    ax1 = fig.add_subplot(111)

    ax1.plot(t, nq, linewidth=1.8, label="Queue Length Nq(t)")
    ax1.plot(t, ns, linewidth=1.6, label="In Service Ns(t)")
    ax1.plot(t, c, linewidth=1.6, label="Active Capacity c(t)")

    for idx, (a, b, rname) in enumerate(segments):
        ax1.axvspan(
            t[a],
            t[b],
            alpha=0.08,
            label=f"Regime: {rname}" if idx == 0 else None,
        )

    policy_idx = np.where(policy == 1)[0]
    if policy_idx.size > 0:
        ax1.axvline(
            t[int(policy_idx[0])],
            linestyle="--",
            linewidth=1.6,
            label="Policy Activation"
        )

    ax1.set_xlabel("Time (minutes)")
    ax1.set_ylabel("Count (patients / servers)")
    ax1.set_ylim(0, max(int(np.max(nq)), int(np.max(ns)), int(np.max(c))) + 2)

    ax2 = ax1.twinx()
    ax2.plot(t, rho, linestyle=":", linewidth=1.6, label="Traffic Intensity ρ(t)")
    ax2.set_ylabel("ρ(t)")

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()

    # Extra space below for legend
    fig.subplots_adjust(bottom=0.22)

    # Put legend below the chart
    fig.legend(
        h1 + h2,
        l1 + l2,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=3,
        frameon=True
    )

    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_figure_2_heatmap(summary_csv: str, out_path: str, fixed_delta_c: int = 1) -> None:
    rows = read_csv(summary_csv)

    # Filter by delta_c
    filt = [r for r in rows if to_int(r["delta_c"]) == fixed_delta_c]

    s_vals = sorted({to_float(r["s"]) for r in filt})
    tau_vals = sorted({to_float(r["tau"]) for r in filt})

    s_index = {s: i for i, s in enumerate(s_vals)}
    tau_index = {tau: j for j, tau in enumerate(tau_vals)}

    # Matrix Z[tau, s] = mean_Tover
    Z = np.full((len(tau_vals), len(s_vals)), np.nan, dtype=float)
    for r in filt:
        s = to_float(r["s"])
        tau = to_float(r["tau"])
        z = to_float(r["mean_Tover"])
        Z[tau_index[tau], s_index[s]] = z

    fig = plt.figure(figsize=(8, 5.5))
    ax = fig.add_subplot(111)

    im = ax.imshow(Z, aspect="auto", origin="lower")

    ax.set_xticks(range(len(s_vals)))
    ax.set_xticklabels([str(s) for s in s_vals])
    ax.set_yticks(range(len(tau_vals)))
    ax.set_yticklabels([str(int(t)) if float(t).is_integer() else str(t) for t in tau_vals])

    ax.set_xlabel("Surge Multiplier (s)")
    ax.set_ylabel("Policy Lag (τ, minutes)")
    ax.set_title(f"Overload Duration Across Surge and Policy Lag (Δc = {fixed_delta_c})")

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Mean Overload Duration (minutes)")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_figure_3_recovery_vs_tau(summary_csv: str, out_path: str, fixed_s: float = 1.5) -> None:
    rows = read_csv(summary_csv)

    # Filter by fixed s
    filt = [r for r in rows if math.isclose(to_float(r["s"]), fixed_s, rel_tol=0.0, abs_tol=1e-12)]

    tau_vals = sorted({to_float(r["tau"]) for r in filt})
    dc_vals = sorted({to_int(r["delta_c"]) for r in filt})

    fig = plt.figure(figsize=(8.5, 6.5))
    ax = fig.add_subplot(111)

    for dc in dc_vals:
        sub = [r for r in filt if to_int(r["delta_c"]) == dc]
        m = {to_float(r["tau"]): to_float(r["mean_Trec"]) for r in sub}
        y = [m.get(tau, np.nan) for tau in tau_vals]
        ax.plot(tau_vals, y, marker="o", linewidth=1.8, label=f"Δc = {dc}")

    ax.set_xlabel("Policy Lag (τ, minutes)")
    ax.set_ylabel("Mean Recovery Time (minutes)")
    ax.set_title(f"Recovery Time vs Policy Lag (s = {fixed_s})")

    # Extra space below for legend
    fig.subplots_adjust(bottom=0.22)

    # Put legend below the chart
    fig.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=3,
        frameon=True
    )

    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

def main() -> None:
    ensure_dir(FIG_DIR)

    fig1_path = os.path.join(FIG_DIR, "fig1_timeline.png")
    fig2_path = os.path.join(FIG_DIR, "fig2_heatmap_tover.png")
    fig3_path = os.path.join(FIG_DIR, "fig3_recovery_vs_tau.png")

    if os.path.exists(TIMELINE_CSV):
        plot_figure_1_timeline(TIMELINE_CSV, fig1_path)
        print(f"Wrote: {fig1_path}")
    else:
        print(f"Missing: {TIMELINE_CSV} (run the simulator first)")

    if os.path.exists(SUMMARY_CSV):
        plot_figure_2_heatmap(SUMMARY_CSV, fig2_path, fixed_delta_c=1)
        print(f"Wrote: {fig2_path}")

        plot_figure_3_recovery_vs_tau(SUMMARY_CSV, fig3_path, fixed_s=1.5)
        print(f"Wrote: {fig3_path}")
    else:
        print(f"Missing: {SUMMARY_CSV} (run the simulator first)")


if __name__ == "__main__":
    main()
