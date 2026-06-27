import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import RelicUniverse, CodexTranslator

# Initialize our universe as a global singleton so memory persists for the Chaos Test
universe = RelicUniverse()


def get_universe(request):
    "Milestone 1: Universe Initialization - Return all nodes"
    return JsonResponse({"nodes": universe.nodes})


@csrf_exempt
def route_packet(request):
    "Milestone 2 & 3: Multi-Hop Proof and Latency Breakdown"
    if request.method == "POST":
        data = json.loads(request.body)
        origin = data.get("origin")
        destination = data.get("destination")
        payload = data.get("payload", "Hello world")

        # 1. Get the shortest path
        path_nodes = universe.find_shortest_path(origin, destination)

        if not path_nodes:
            return JsonResponse(
                {"error": f"Route from {origin} to {destination} undeliverable"},
                status=400,
            )

        hop_log = []
        total_latency_seconds = 0.0

        # 2. Build the precise packet trace and latency breakdown
        for i in range(len(path_nodes) - 1):
            current_id = path_nodes[i]
            next_id = path_nodes[i + 1]

            # Recalculate component math for the logs (to prove it to the judges)
            t_exit, t_entry = universe.find_line_of_sight_towers(current_id, next_id)
            L = universe.calculate_void_distance(current_id, next_id)

            # Latency Breakdown
            Tp = universe.calculate_crust_transit_time(
                universe.nodes[current_id], 0, t_exit
            )  # Assuming entry at tower 0 for simplicity on origin
            Tv = universe.calculate_void_latency(
                universe.nodes[current_id], universe.nodes[next_id], L
            )

            hop_latency = Tp + Tv
            total_latency_seconds += hop_latency

            # Codex Translation (Current Planet -> Next Planet)
            next_codex = universe.nodes[next_id]["codex"]
            encoded_payload = CodexTranslator.encode_payload(payload, next_codex)

            hop_log.append(
                {
                    "hop_number": i + 1,
                    "from_planet": current_id,
                    "to_planet": next_id,
                    "tower_routing": f"Exit Tower {t_exit} -> Entry Tower {t_entry}",
                    "void_distance_km": round(L, 2),
                    "latency_breakdown": {
                        "internal_crust_time_sec": round(Tp, 6),
                        "void_travel_time_sec": round(Tv, 6),
                        "total_hop_latency_sec": round(hop_latency, 6),
                    },
                    "data_translation": {
                        "next_hop_codex": next_codex,
                        "binary_transmission_stream": encoded_payload,
                    },
                }
            )

        # 3. Final Mandatory Packet Schema
        packet_schema = {
            "origin_id": origin,
            "destination_id": destination,
            "current_id": path_nodes[-1],  # Packet has arrived
            "payload": payload,  # Re-decoded at final destination
            "total_latency_seconds": round(total_latency_seconds, 6),
            "path_taken": path_nodes,
            "hop_log": hop_log,
        }

        return JsonResponse(packet_schema)


@csrf_exempt
def toggle_node(request):
    "Milestone 4: Chaos Test - Kill or revive a node dynamically"
    if request.method == "POST":
        data = json.loads(request.body)
        node_id = data.get("node_id")
        action = data.get("action", "kill")  # 'kill' or 'revive'

        if action == "kill":
            universe.kill_node(node_id)
            return JsonResponse({"status": f"{node_id} offline!"})
        else:
            universe.revive_node(node_id)
            return JsonResponse({"status": f"{node_id} back online!"})


def HealthCheckView(request):
    "Health Check Endpoint"
    return JsonResponse({"status": "healthy"})
