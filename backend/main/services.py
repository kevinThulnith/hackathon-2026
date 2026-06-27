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
        if n == 0: return "0"
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
# 2. PHYSICS & LATENCY ENGINE
# ==========================================
class RelicUniverse:
    def __init__(self, config_filename="universe-config.json"):
        # Look for the config file in the base directory
        config_path = os.path.join(settings.BASE_DIR, config_filename)
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        self.metadata = data["universe_metadata"]
        self.C = self.metadata.get("speed_of_light_kms", 300000.0)
        self.L_max = self.metadata.get("max_void_hop_distance_km", 50000000.0)
        self.S = self.metadata.get("coordinate_scale_unit_km", 100000.0)
        self.delta_t = self.metadata.get("tower_processing_delay_ms", 7.0)
        self.fiber_f = self.metadata.get("fiber_speed_fraction", 0.67)
        
        self.nodes = {node["id"]: node for node in data["nodes"]}
        self.dead_nodes = set()

    # --- Resilience Methods ---
    def kill_node(self, node_id):
        self.dead_nodes.add(node_id)
        
    def revive_node(self, node_id):
        self.dead_nodes.discard(node_id)
        
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
        # Top is 90 degrees (or pi/2) in standard math, but let's use 0 degrees at top, clockwise.
        # Angle in degrees = (tower_index / N) * 360
        angle_deg = (tower_index / N) * 360.0
        return angle_deg

    def calculate_crust_transit_time(self, planet, entry_tower_idx, exit_tower_idx):
        """Formula 3: Internal Crust Transit Time (Tp)"""
        N = planet["active_towers"]
        r = planet["radius_km"]
        
        if entry_tower_idx == exit_tower_idx:
            s = 0
            m = 1 # dedup case: entry = exit
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
        Tp = fiber_time + tower_delay
        
        # NOTE: Tp is usually in seconds (or ms). 
        # Fiber time is in seconds. Let's convert tower_delay (ms) to seconds for consistency:
        tower_delay_sec = tower_delay / 1000.0
        
        return fiber_time + tower_delay_sec

    def find_line_of_sight_towers(self, node1_id, node2_id):
        """
        Line of sight rule: 'The tower pair whose positions minimize the 
        straight-line void distance between them is used.'
        """
        p1, p2 = self.nodes[node1_id], self.nodes[node2_id]
        
        # Calculate angle from p1 to p2
        dx = p2["x"] - p1["x"]
        dy = p2["y"] - p1["y"]
        
        # standard math angle (0 is right, counter-clockwise)
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad) % 360
        
        # Convert standard angle to our "top is 0, clockwise" system
        # y is positive up (assuming standard Cartesian). 
        # Standard: top is 90 deg.
        target_angle_1 = (90 - angle_deg) % 360
        target_angle_2 = (target_angle_1 + 180) % 360 # opposite direction for p2
        
        # Find closest tower on p1 to target_angle_1
        N1 = p1["active_towers"]
        best_t1 = min(range(N1), key=lambda i: abs((i * 360 / N1) - target_angle_1))
        
        # Find closest tower on p2 to target_angle_2
        N2 = p2["active_towers"]
        best_t2 = min(range(N2), key=lambda i: abs((i * 360 / N2) - target_angle_2))
        
        return best_t1, best_t2
    
    def find_shortest_path(self, origin_id, dest_id):
        """Uses Dijkstra's Algorithm to find the lowest-latency path."""
        import heapq
        
        # Priority queue stores: (total_latency_seconds, current_node_id, entry_tower_idx)
        pq = [(0, origin_id, 0)] 
        
        # Track the shortest latency to each node and the path
        distances = {node: float('infinity') for node in self.nodes}
        distances[origin_id] = 0
        previous = {node: None for node in self.nodes}
        
        while pq:
            curr_latency, curr_id, curr_entry_tower = heapq.heappop(pq)
            
            if curr_latency > distances[curr_id]:
                continue
                
            if curr_id == dest_id:
                break # Reached the destination!
                
            for neighbor_id in self.nodes:
                if neighbor_id == curr_id or not self.is_active(neighbor_id):
                    continue
                    
                # 1. Calculate Void Distance
                L = self.calculate_void_distance(curr_id, neighbor_id)
                if L > self.L_max:
                    continue # Exceeds wireless threshold, invalid hop
                    
                # 2. Line of Sight Towers
                t_exit, t_neighbor_entry = self.find_line_of_sight_towers(curr_id, neighbor_id)
                
                # 3. Calculate delays
                # Tp (Crust Transit) on current planet
                Tp = self.calculate_crust_transit_time(self.nodes[curr_id], curr_entry_tower, t_exit)
                # Tv (Void Transit) to neighbor
                Tv = self.calculate_void_latency(self.nodes[curr_id], self.nodes[neighbor_id], L)
                
                new_latency = curr_latency + Tp + Tv
                
                if new_latency < distances[neighbor_id]:
                    distances[neighbor_id] = new_latency
                    previous[neighbor_id] = {
                        "node": curr_id,
                        "exit_tower": t_exit,
                        "entry_tower": t_neighbor_entry,
                        "hop_Tp": Tp,
                        "hop_Tv": Tv
                    }
                    heapq.heappush(pq, (new_latency, neighbor_id, t_neighbor_entry))

        # Reconstruct path
        if distances[dest_id] == float('infinity'):
            return None # Undeliverable
            
        path = []
        curr = dest_id
        while curr:
            path.insert(0, curr)
            if previous[curr]:
                curr = previous[curr]["node"]
            else:
                curr = None
                
        return path