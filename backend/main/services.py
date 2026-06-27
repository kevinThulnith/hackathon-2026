import json
import math
import os
from django.conf import settings


# ==========================================
# 1. CODEX TRANSLATOR
# ==========================================
class CodexTranslator:
    CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @classmethod
    def to_base(cls, n, b):
        if n == 0:
            return "0"
        digits = []
        while n > 0:
            digits.append(cls.CHARS[n % b])
            n //= b
        return "".join(digits[::-1])

    @classmethod
    def from_base(cls, s, b):
        n = 0
        for char in str(s):
            n = n * b + cls.CHARS.index(char.upper())
        return n

    @classmethod
    def encode_payload(cls, text, target_codex):
        return [cls.to_base(ord(c), target_codex) for c in text]


# ==========================================
# Custom exceptions so views can tell errors apart
# and return the right HTTP status / message instead
# of a generic 500 or a misleading 400.
# ==========================================
class UnknownNodeError(Exception):
    """Raised when a node_id doesn't exist in the universe at all."""

    def __init__(self, node_id):
        self.node_id = node_id
        super().__init__(f"Unknown node_id: '{node_id}'")


class NodeOfflineError(Exception):
    """Raised when a node exists but has been killed via toggle_node."""

    def __init__(self, node_id):
        self.node_id = node_id
        super().__init__(f"Node '{node_id}' is currently offline")


# ==========================================
# 2. PHYSICS & LATENCY ENGINE
# ==========================================
class RelicUniverse:
    def __init__(self, config_filename="universe-config.json"):
        # Look for the config file in the base directory
        config_path = os.path.join(settings.BASE_DIR, config_filename)
        with open(config_path, "r") as f:
            data = json.load(f)

        self.metadata = data["universe_metadata"]
        self.C = self.metadata.get("speed_of_light_kms", 300000.0)
        self.L_max = self.metadata.get("max_void_hop_distance_km", 50000000.0)
        self.S = self.metadata.get("coordinate_scale_unit_km", 100000.0)
        self.delta_t = self.metadata.get("tower_processing_delay_ms", 7.0)
        self.fiber_f = self.metadata.get("fiber_speed_fraction", 0.67)

        self.nodes = {node["id"]: node for node in data["nodes"]}
        self.dead_nodes = set()

        # Case-insensitive lookup map: "aegis" -> "Aegis"
        # This is what was silently breaking requests before: node IDs
        # are case-sensitive ("Aegis", "Boreas", ...), so any client
        # sending a different case (or a typo) caused a raw KeyError
        # deep inside Dijkstra, which Django turned into an opaque 500.
        self._id_lookup = {node_id.lower(): node_id for node_id in self.nodes}

    # --- Node resolution / validation ---
    def resolve_node_id(self, raw_id):
        """
        Normalizes a client-supplied node_id to the canonical stored ID.
        Raises UnknownNodeError if it doesn't match any known node,
        even case-insensitively.
        """
        if raw_id is None:
            raise UnknownNodeError(raw_id)
        canonical = self._id_lookup.get(str(raw_id).strip().lower())
        if canonical is None:
            raise UnknownNodeError(raw_id)
        return canonical

    # --- Resilience Methods ---
    def kill_node(self, node_id):
        canonical = self.resolve_node_id(node_id)
        self.dead_nodes.add(canonical)
        return canonical

    def revive_node(self, node_id):
        canonical = self.resolve_node_id(node_id)
        self.dead_nodes.discard(canonical)
        return canonical

    def is_active(self, node_id):
        return node_id not in self.dead_nodes

    # --- Math Formulas ---
    def calculate_void_distance(self, node1_id, node2_id):
        """Formula 1: Void Distance (L) - Simplified center-to-center minus radius and atmos"""
        p1, p2 = self.nodes[node1_id], self.nodes[node2_id]

        dx = p2["x"] - p1["x"]
        dy = p2["y"] - p1["y"]
        center_dist = math.sqrt(dx**2 + dy**2) * self.S

        r1, h1 = p1["radius_km"], p1["atmosphere_thickness_km"]
        r2, h2 = p2["radius_km"], p2["atmosphere_thickness_km"]

        L = center_dist - (r1 + h1) - (r2 + h2)
        return L

    def calculate_void_latency(self, p1, p2, L):
        """Formula 2: Void Travel Time (Tv)"""
        h1, n1 = p1["atmosphere_thickness_km"], p1["refraction_index"]
        h2, n2 = p2["atmosphere_thickness_km"], p2["refraction_index"]

        Tv = ((h1 * n1) + (h2 * n2) + L) / self.C
        return Tv

    def get_tower_angular_position(self, planet, tower_index):
        """Calculates angular position of a tower (Tower 0 is at top/positive y, clockwise)"""
        N = planet["active_towers"]
        angle_deg = (tower_index / N) * 360.0
        return angle_deg

    def calculate_crust_transit_time(self, planet, entry_tower_idx, exit_tower_idx):
        """Formula 3: Internal Crust Transit Time (Tp)"""
        N = planet["active_towers"]
        r = planet["radius_km"]

        if entry_tower_idx == exit_tower_idx:
            s = 0
            m = 1  # dedup case: entry = exit
        else:
            # Shortest path around the ring (clockwise vs counter-clockwise)
            diff = abs(exit_tower_idx - entry_tower_idx)
            s = min(diff, N - diff)
            m = s + 1

        # Fiber transit time + tower processing delay
        if s == 0:
            fiber_time = 0
        else:
            fiber_time = (2 * math.pi * r * s) / (N * self.fiber_f * self.C)

        tower_delay = m * self.delta_t

        # NOTE: Tp is usually in seconds (or ms).
        # Fiber time is in seconds. Convert tower_delay (ms) to seconds for consistency:
        tower_delay_sec = tower_delay / 1000.0

        return fiber_time + tower_delay_sec

    def find_line_of_sight_towers(self, node1_id, node2_id):
        """
        Line of sight rule: 'The tower pair whose positions minimize the
        straight-line void distance between them is used.'
        """
        p1, p2 = self.nodes[node1_id], self.nodes[node2_id]

        dx = p2["x"] - p1["x"]
        dy = p2["y"] - p1["y"]

        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad) % 360

        target_angle_1 = (90 - angle_deg) % 360
        target_angle_2 = (target_angle_1 + 180) % 360  # opposite direction for p2

        N1 = p1["active_towers"]
        best_t1 = min(range(N1), key=lambda i: abs((i * 360 / N1) - target_angle_1))

        N2 = p2["active_towers"]
        best_t2 = min(range(N2), key=lambda i: abs((i * 360 / N2) - target_angle_2))

        return best_t1, best_t2

    def find_shortest_path(self, origin_id, dest_id):
        """
        Uses Dijkstra's Algorithm to find the lowest-latency path.

        Raises UnknownNodeError if origin_id/dest_id aren't real nodes
        (previously this would KeyError deep in the loop, or silently
        return None and get reported back as a misleading 400).

        Returns None only for the genuine "no route exists" case
        (e.g. a required relay node is dead, or every hop exceeds L_max).
        """
        import heapq

        # Validate + normalize both endpoints up front. This is the fix:
        # before, a bad/mis-cased ID here either KeyError'd inside the
        # Dijkstra loop (-> 500) or, if it happened to match a key by luck,
        # could be silently treated as "no path" (-> confusing 400).
        origin_id = self.resolve_node_id(origin_id)
        dest_id = self.resolve_node_id(dest_id)

        pq = [(0, origin_id, 0)]

        distances = {node: float("infinity") for node in self.nodes}
        distances[origin_id] = 0
        previous = {node: None for node in self.nodes}

        while pq:
            curr_latency, curr_id, curr_entry_tower = heapq.heappop(pq)

            if curr_latency > distances[curr_id]:
                continue

            if curr_id == dest_id:
                break  # Reached the destination!

            for neighbor_id in self.nodes:
                if neighbor_id == curr_id or not self.is_active(neighbor_id):
                    continue
                if not self.is_active(curr_id):
                    continue

                L = self.calculate_void_distance(curr_id, neighbor_id)
                if L > self.L_max:
                    continue  # Exceeds wireless threshold, invalid hop

                t_exit, t_neighbor_entry = self.find_line_of_sight_towers(
                    curr_id, neighbor_id
                )

                Tp = self.calculate_crust_transit_time(
                    self.nodes[curr_id], curr_entry_tower, t_exit
                )
                Tv = self.calculate_void_latency(
                    self.nodes[curr_id], self.nodes[neighbor_id], L
                )

                new_latency = curr_latency + Tp + Tv

                if new_latency < distances[neighbor_id]:
                    distances[neighbor_id] = new_latency
                    previous[neighbor_id] = {
                        "node": curr_id,
                        "exit_tower": t_exit,
                        "entry_tower": t_neighbor_entry,
                        "hop_Tp": Tp,
                        "hop_Tv": Tv,
                    }
                    heapq.heappush(pq, (new_latency, neighbor_id, t_neighbor_entry))

        if distances[dest_id] == float("infinity"):
            return None  # Genuinely undeliverable (dead relay node / out of range)

        path = []
        curr = dest_id
        while curr:
            path.insert(0, curr)
            if previous[curr]:
                curr = previous[curr]["node"]
            else:
                curr = None

        return path
