"""
node.py — Gossip-based Membership Node

Mỗi node:
  - Có 1 IP address giả lập (ví dụ: "10.0.0.1")
  - Duy trì PARTIAL VIEW (live_list chỉ là tập con ban đầu)
  - Gossip state với neighbor → dần biết toàn mạng
"""

import random

# ── Tạo pool 100 IP giả lập ──────────────────────────────────
def make_ip_pool(n: int = 100) -> dict[int, str]:
    """Map node_id → IP string, ví dụ 0 → '10.0.0.1'"""
    return {i: f"10.0.{i // 256}.{i % 256 + 1}" for i in range(n)}


class Node:
    def __init__(
        self,
        node_id: int,
        all_ids: list[int],
        ip_pool: dict[int, str],
        partial_view_size: int = 10,  
    ):
        self.id   = node_id
        self.ip   = ip_pool[node_id]
        self.alive = True 

        # Partial View: chỉ biết một tập con ngẫu nhiên ban đầu
        others = [i for i in all_ids if i != node_id]
        initial = random.sample(others, min(partial_view_size, len(others)))
        self.live_list: set[int] = set(initial)
        self.dead_list: set[int] = set()

    # ------------------------------------------------------------------ #
    # Gossip payload gửi đi
    # ------------------------------------------------------------------ #
    def get_payload(self) -> dict:
        return {
            "sender":    self.id,
            "live_list": set(self.live_list),
            "dead_list": set(self.dead_list),
        }

    # ------------------------------------------------------------------ #
    # Merge state nhận được từ peer
    # dead > live (ưu tiên trạng thái chết)
    # ------------------------------------------------------------------ #
    def merge(self, payload: dict) -> None:
        incoming_live = payload["live_list"]
        incoming_dead = payload["dead_list"]

        self.dead_list |= incoming_dead
        self.live_list |= incoming_live
        self.live_list -= self.dead_list   # dead luôn thắng
        self.live_list.discard(self.id)    # không tự đưa mình vào live_list

    # ------------------------------------------------------------------ #
    # Detect failure: ping một node, nếu dead → cập nhật local state
    # ------------------------------------------------------------------ #
    def detect_failure(self, target: "Node") -> bool:
        """
        Trả về True nếu phát hiện target chết.
        Trong simulation: target.alive == False → ping fail.
        """
        if not target.alive:
            self.dead_list.add(target.id)
            self.live_list.discard(target.id)
            return True
        return False


    def pick_neighbors(self, k: int = 3) -> list[int]:
        candidates = list(self.live_list)
        return random.sample(candidates, min(k, len(candidates)))

    def __repr__(self):
        status = "ALIVE" if self.alive else "DEAD "
        return (f"Node({self.id:03d}|{self.ip}|{status}) "
                f"live={len(self.live_list)} dead={len(self.dead_list)}")