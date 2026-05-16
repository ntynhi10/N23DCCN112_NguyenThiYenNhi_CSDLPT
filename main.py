"""
main.py — Entry point của Gossip-based Membership Protocol

Chạy:  python main.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from simulation import GossipSimulation
from analysis import main as run_analysis


if __name__ == "__main__":
    run_analysis()
    # ── Test Partial View Init ──────────────────────────
    print("\n" + "=" * 65)
    print("  TEST: Kiểm tra khởi tạo Partial View")
    print("=" * 65)

    sim = GossipSimulation(n_nodes=100, partial_view_size=10, seed=42)

    for node_id in [0, 5, 33, 67, 99]:
        node = sim.nodes[node_id]
        print(f"Node {node_id:02d} ({node.ip}):")
        print(f"  live_list size = {len(node.live_list)}")
        print(f"  live_list      = {sorted(node.live_list)}")
        print(f"  Tu liet ke minh? {node_id in node.live_list}")
        print()