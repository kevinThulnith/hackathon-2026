import json


# ==========================================
# 1. CODEX TRANSLATOR (Data Encoding)
# ==========================================
class CodexTranslator:
    CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @classmethod
    def to_base(cls, n, b):
        """Converts an integer to a string representation in the given base."""
        if n == 0:
            return "0"
        digits = []
        while n > 0:
            digits.append(cls.CHARS[n % b])
            n //= b
        return "".join(digits[::-1])

    @classmethod
    def from_base(cls, s, b):
        """Converts a string representation in a given base back to an integer."""
        n = 0
        for char in str(s):
            n = n * b + cls.CHARS.index(char.upper())
        return n

    @classmethod
    def encode_payload(cls, text, target_codex):
        """Converts raw ASCII text into a list of base-N encoded strings."""
        return [cls.to_base(ord(c), target_codex) for c in text]

    @classmethod
    def decode_payload(cls, encoded_list, current_codex):
        """Converts a list of base-N encoded strings back to raw ASCII text."""
        return "".join(chr(cls.from_base(x, current_codex)) for x in encoded_list)


# ==========================================
# 2. UNIVERSE CONFIGURATION ENGINE
# ==========================================
class RelicUniverse:
    def __init__(self, config_path="universe-config.json"):
        with open(config_path, "r") as f:
            data = json.load(f)

        self.metadata = data["universe_metadata"]

        # Load constraints with safe fallbacks based on PDF instructions
        self.speed_of_light = self.metadata.get("speed_of_light_kms", 300000.0)
        self.max_void_hop = self.metadata.get("max_void_hop_distance_km", 50000000.0)
        self.scale_unit = self.metadata.get("coordinate_scale_unit_km", 100000.0)
        self.tower_delay = self.metadata.get("tower_processing_delay_ms", 7.0)
        self.fiber_fraction = self.metadata.get("fiber_speed_fraction", 0.67)

        # Load planets into a dictionary for easy O(1) lookup
        self.nodes = {node["id"]: node for node in data["nodes"]}

        # State tracker for the "Chaos Test" (Dynamic Rerouting)
        self.dead_nodes = set()

    def kill_node(self, node_id):
        """Marks a node as dead for Milestone 4 (Chaos Test)."""
        self.dead_nodes.add(node_id)

    def revive_node(self, node_id):
        """Revives a node."""
        self.dead_nodes.discard(node_id)

    def is_active(self, node_id):
        return node_id not in self.dead_nodes


# ==========================================
# QUICK TEST (Run this to verify it works!)
# ==========================================
if __name__ == "__main__":
    # Test Milestone 1: Initialization
    universe = RelicUniverse()
    print(f"Loaded {len(universe.nodes)} planets successfully.")
    print(f"Max Void Hop: {universe.max_void_hop} km")

    # Test Data Translation (Matches PDF exactly!)
    message = "Hello world"

    # Planet B is Base 5
    encoded_base_5 = CodexTranslator.encode_payload(message, 5)
    print(f"\n'Hello world' in Base 5: {encoded_base_5}")
    # Expected first char: 242

    # Planet C is Base 14
    encoded_base_14 = CodexTranslator.encode_payload(message, 14)
    print(f"'Hello world' in Base 14: {encoded_base_14}")
    # Expected: ['52', '73', '7A', '7A', '7D', '24', '87', '7D', '82', '7A', '72']
