"""
analysis.py — Vẽ chart phân tích Gossip-based Membership Protocol

Metric chính:
  "Percentage of peers with an accurate Live List over time intervals"
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from simulation import GossipSimulation


def plot_accurate_livelist(result, ax, title=""):
    history  = result["history"]
    rounds   = [h["round"] for h in history]
    pct_acc  = [h["pct_accurate"] * 100 for h in history]

    kill_r   = result["kill_round"]
    detect_r = result["detect_round"]

    ax.step(rounds, pct_acc, where='post', color="#E63946", lw=2.5,
            label="% peers with accurate Live List")
    ax.fill_between(rounds, pct_acc, alpha=0.12, color="#E63946", step='post')

    if kill_r:
        ax.axvline(kill_r, color="#F4A261", lw=2, ls="--",
                   label=f"Dead node introduced (r={kill_r})")
    if detect_r:
        ax.axvline(detect_r, color="#2A9D8F", lw=2, ls="--",
                   label=f"100% accurate (r={detect_r}, Δ={result['detection_time']}r)")

    ax.axhline(100, color="#aaa", lw=0.8)
    ax.set_xlabel("Time Interval (round)", fontsize=11)
    ax.set_ylabel("% Peers with Accurate Live List", fontsize=11)
    ax.set_ylim(-5, 112)
    ax.set_xlim(rounds[0], rounds[-1])
    ax.set_title(title or f"N={result['n_nodes']}, partial_view={result['partial_view']}, fanout={result['fanout']}",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    ax.set_facecolor("#f9f9fb")


def experiment_fanout(n_nodes=100, fanouts=None, partial_view=10,
                      kill_round=10, max_rounds=120, repeats=5):
    if fanouts is None:
        fanouts = [1, 2, 3, 5, 8]
    results = {}
    for f in fanouts:
        times = []
        for r in range(repeats):
            sim = GossipSimulation(n_nodes=n_nodes, partial_view_size=partial_view,
                                   gossip_fanout=f, kill_round=kill_round,
                                   max_rounds=max_rounds, seed=r * 13)
            res = sim.run(verbose=False)
            if res["detection_time"] is not None:
                times.append(res["detection_time"])
        results[f] = times
    return results


def plot_fanout_bar(fanout_results, ax):
    fanouts = sorted(fanout_results.keys())
    means   = [np.mean(fanout_results[f]) if fanout_results[f] else np.nan for f in fanouts]
    stds    = [np.std(fanout_results[f]) if len(fanout_results[f]) > 1 else 0 for f in fanouts]
    palette = ["#E63946", "#F4A261", "#2A9D8F", "#457B9D", "#6A4C93"]

    bars = ax.bar([str(f) for f in fanouts], means, yerr=stds,
                  color=palette[:len(fanouts)], capsize=5, edgecolor="white", linewidth=1.2)
    for bar, m in zip(bars, means):
        if not np.isnan(m):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                    f"{m:.1f}r", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xlabel("Gossip Fanout (k)", fontsize=11)
    ax.set_ylabel("Detection Time (rounds)", fontsize=11)
    ax.set_title("Detection Time vs Gossip Fanout", fontsize=12, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.set_facecolor("#f9f9fb")


def main():
    print("🔬 Running Gossip-based Membership experiments...\n")

    print("  [1/3] Single run — N=100, fanout=3, partial_view=10")
    sim1 = GossipSimulation(n_nodes=100, partial_view_size=10,
                            gossip_fanout=3, kill_round=10, max_rounds=60, seed=42)
    res1 = sim1.run(verbose=True)

    print("\n  [2/3] Single run — N=100, fanout=1, partial_view=10 (slow)")
    sim2 = GossipSimulation(n_nodes=100, partial_view_size=10,
                            gossip_fanout=1, kill_round=10, max_rounds=80, seed=42)
    res2 = sim2.run(verbose=False)

    print("\n  [3/3] Fanout sweep...")
    fanout_data = experiment_fanout(fanouts=[1, 2, 3, 5, 8], repeats=5)

    fig = plt.figure(figsize=(15, 10))
    fig.suptitle(
        'Gossip-based Membership Protocol — "Who is Online?"\n'
        'Dataset: 100 simulated IP addresses  |  '
        'Metric: % Peers with Accurate Live List over Time',
        fontsize=13, fontweight="bold", y=1.01
    )

    ax1 = fig.add_subplot(2, 2, 1)  
    ax2 = fig.add_subplot(2, 2, 2) 
    ax3 = fig.add_subplot(2, 1, 2) 

    plot_accurate_livelist(res1, ax1,
        title="% Accurate Live List over Time — fanout=3 (fast)")
    plot_accurate_livelist(res2, ax2,
        title="% Accurate Live List over Time — fanout=1 (slow)")
    plot_fanout_bar(fanout_data, ax3)

    plt.tight_layout()
    out = "gossip_analysis.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"\n✅  Chart saved → {out}")
    return out


if __name__ == "__main__":
    main()