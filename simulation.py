"""
simulation.py — Gossip-based Membership Simulation Engine

Dataset : 100 IP addresses (simulated, e.g. "10.0.0.1" … "10.0.0.100")
Task    : Peers maintain a PARTIAL VIEW; periodically swap Live Lists with a neighbor
Analysis: Introduce a Dead Node → measure how long until whole network knows
Metric  : % peers with accurate Live List over time intervals
"""

import random
from typing import Optional
from node import Node, make_ip_pool


# ============================================================ #
#  Metrics
# ============================================================ #

def pct_accurate_live_list(nodes: list[Node], true_dead: set[int]) -> float:
    """
    ★ Metric chính của đề bài:
    % peers có Live List CHÍNH XÁC (không chứa bất kỳ node dead nào)
    """
    alive_nodes = [n for n in nodes if n.id not in true_dead]
    if not alive_nodes:
        return 1.0
    correct = sum(
        1 for n in alive_nodes
        if not (n.live_list & true_dead)   # live_list ∩ dead_set = ∅
    )
    return correct / len(alive_nodes)


def pct_knows_specific_dead(nodes: list[Node], dead_id: int) -> float:
    """
    % peers biết node dead_id đã chết (dùng để đo detection time)
    """
    alive_nodes = [n for n in nodes if n.id != dead_id]
    if not alive_nodes:
        return 1.0
    correct = sum(1 for n in alive_nodes if dead_id not in n.live_list)
    return correct / len(alive_nodes)





# ============================================================ #
#  Core Simulation
# ============================================================ #

class GossipSimulation:
    def __init__(
        self,
        n_nodes: int = 100,
        partial_view_size: int = 10,   # mỗi node ban đầu chỉ biết 10 peer
        gossip_fanout: int = 3,
        kill_round: int = 10,
        max_rounds: int = 80,
        seed: Optional[int] = None,
    ):
        if seed is not None:
            random.seed(seed)

        self.n_nodes           = n_nodes
        self.partial_view_size = partial_view_size
        self.fanout            = gossip_fanout
        self.kill_round        = kill_round
        self.max_rounds        = max_rounds

        # IP pool: node_id → IP string
        self.ip_pool = make_ip_pool(n_nodes)

        # Khởi tạo nodes với PARTIAL VIEW
        all_ids = list(range(n_nodes))
        self.nodes: dict[int, Node] = {
            i: Node(i, all_ids, self.ip_pool, partial_view_size)
            for i in all_ids
        }

        self.dead_id: Optional[int] = None
        self.true_dead: set[int]    = set()
        self.history: list[dict]    = []

    # -------------------------------------------------- #

    def kill_node(self, node_id: Optional[int] = None) -> int:
        if node_id is None:
            node_id = random.choice(list(self.nodes.keys()))
        self.nodes[node_id].alive = False
        self.dead_id = node_id
        self.true_dead.add(node_id)
        return node_id

    # -------------------------------------------------- #

    def gossip_round(self) -> None:
        """
        Một round gossip — mỗi node ALIVE:
          1. Chọn k neighbor ngẫu nhiên từ live_list (partial view)
          2. Ping neighbor: nếu dead → đánh dấu, skip trao đổi
          3. Push own state → neighbor merge
          4. Pull neighbor state → self merge  (push-pull)
        """
        node_list = list(self.nodes.values())
        random.shuffle(node_list)

        for node in node_list:
            if not node.alive:
                continue

            neighbors_ids = node.pick_neighbors(self.fanout)

            for nid in neighbors_ids:
                neighbor = self.nodes[nid]

                # Ping (failure detection)
                failed = node.detect_failure(neighbor)

                if not failed:
                    # Push
                    neighbor.merge(node.get_payload())
                    # Pull (push-pull)
                    node.merge(neighbor.get_payload())

    # -------------------------------------------------- #

    def run(self, verbose: bool = True) -> dict:
        t_kill         = None
        t_detect       = None
        detection_time = None

        if verbose:
            print("=" * 65)
            print(f"  Gossip-based Membership Protocol — 'Who is Online?'")
            print(f"  Dataset : {self.n_nodes} simulated IP addresses")
            print(f"  Partial View size : {self.partial_view_size} peers per node")
            print(f"  Gossip fanout     : {self.fanout}")
            print(f"  Kill at round     : {self.kill_round}")
            print("=" * 65)

        for rnd in range(1, self.max_rounds + 1):
            if rnd == self.kill_round:
                dead_id = self.kill_node()
                t_kill  = rnd
                if verbose:
                    dead_ip = self.ip_pool[dead_id]
                    print(f"\n💀  Round {rnd}: Node {dead_id} ({dead_ip}) KILLED\n")

            self.gossip_round()

            # ── Metrics ──────────────────────────────────────────
            # Chưa có node nào chết → tất cả live_list đều đúng → 100%
            pct_acc  = pct_accurate_live_list(
                list(self.nodes.values()), self.true_dead
            ) if self.dead_id is not None else 1.0

            pct_know = pct_knows_specific_dead(
                list(self.nodes.values()), self.dead_id
            ) if self.dead_id is not None else 1.0

            entry = {
                "round":          rnd,
                "pct_accurate":   pct_acc,     # ★ metric chính của đề
                "pct_know_dead":  pct_know,    # detection metric
                "killed":         rnd == self.kill_round,
            }
            self.history.append(entry)

            # Detection time: round đầu pct_accurate = 100%
            if pct_acc == 1.0 and t_detect is None and t_kill is not None:
                t_detect       = rnd
                detection_time = t_detect - t_kill

            if verbose and self.dead_id is not None:
                bar_len = int(pct_acc * 30)
                bar = "█" * bar_len + "░" * (30 - bar_len)
                tag = "  ← 100% ACCURATE!" if t_detect == rnd else ""
                print(f"  Round {rnd:03d} | Accurate LiveList [{bar}] "
                      f"{pct_acc*100:5.1f}%{tag}")

        result = {
            "n_nodes":         self.n_nodes,
            "partial_view":    self.partial_view_size,
            "fanout":          self.fanout,
            "kill_round":      t_kill,
            "detect_round":    t_detect,
            "detection_time":  detection_time,
            "dead_id":         self.dead_id,
            "dead_ip":         self.ip_pool.get(self.dead_id) if self.dead_id is not None else None,
            "history":         self.history,
            "ip_pool":         self.ip_pool,
        }

        if verbose:
            print("\n" + "=" * 65)
            if detection_time is not None:
                print(f"  ✅  Detection Time : {detection_time} rounds "
                      f"(killed r={t_kill} → 100% aware r={t_detect})")
            else:
                print(f"  ⚠️   Chưa 100% sau {self.max_rounds} rounds")
            print("=" * 65)

        return result
    